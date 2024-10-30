import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import json

class LoanManager:
    def __init__(self, map_data_path, awards_data_path):
        # Load configuration data
        self.map_data = self.load_json(map_data_path)
        self.awards_data = self.load_json(awards_data_path)
        self.personality_weights = {
            "Conservative": {
                "interest_sensitivity": 0.8,
                "environmental_bonus": 0.3,
                "award_preference": ["IkeaCheck", "HalfInterestRate"]
            },
            "RiskTaker": {
                "interest_sensitivity": 0.4,
                "environmental_bonus": 0.5,
                "award_preference": ["GiftCard", "NoInterestRate"]
            },
            "Innovative": {
                "interest_sensitivity": 0.6,
                "environmental_bonus": 0.8,
                "award_preference": ["IkeaDeliveryCheck", "GiftCard"]
            },
            "Practical": {
                "interest_sensitivity": 0.7,
                "environmental_bonus": 0.6,
                "award_preference": ["IkeaFoodCoupon", "HalfInterestRate"]
            },
            "Spontaneous": {
                "interest_sensitivity": 0.5,
                "environmental_bonus": 0.4,
                "award_preference": ["GiftCard", "IkeaCheck"]
            }
        }

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def calculate_credit_score(self, customer):
        # Basic credit score calculation
        monthly_disposable = customer['income'] - customer['monthlyExpenses']
        debt_ratio = (customer['homeMortgage'] / customer['income']) if customer['income'] > 0 else 1
        
        base_score = (
            (monthly_disposable * 0.4) +
            (customer['capital'] * 0.3) +
            (customer['income'] * 0.3)
        )
        
        # Adjustments
        if customer['hasStudentLoan']:
            base_score *= 0.9
        base_score *= (1 - (customer['numberOfKids'] * 0.05))
        base_score *= (1 - debt_ratio)
        
        return base_score

    def determine_interest_rate(self, customer, credit_score):
        personality = customer['personality']
        base_rate = 0.05  # 5% base rate
        
        # Adjust based on credit score
        credit_adjustment = max(0, (1000 - credit_score) / 10000)
        
        # Adjust based on environmental impact
        env_impact = customer['loan']['environmentalImpact']
        env_adjustment = 0.01 if env_impact > 50 else -0.01
        
        # Personality adjustment
        personality_factor = self.personality_weights[personality]['interest_sensitivity']
        
        final_rate = base_rate + credit_adjustment + env_adjustment
        final_rate *= personality_factor
        
        # Ensure rate stays within reasonable bounds
        return max(0.02, min(0.15, final_rate))

    def generate_award_strategy(self, customer, month, total_months):
        personality = customer['personality']
        preferred_awards = self.personality_weights[personality]['award_preference']
        
        # Early game strategy
        if month < total_months * 0.3:
            award_chance = 0.7
        # Mid game strategy
        elif month < total_months * 0.7:
            award_chance = 0.5
        # Late game strategy
        else:
            award_chance = 0.3
            
        if np.random.random() < award_chance:
            return {
                "Type": "Award",
                "Award": np.random.choice(preferred_awards)
            }
        return {
            "Type": "Skip",
            "Award": "None"
        }

    def generate_game_input(self):
        game_input = {
            "MapName": self.map_data['name'],
            "Proposals": [],
            "Iterations": []
        }

        # Generate loan proposals
        for customer in self.map_data['customers']:
            credit_score = self.calculate_credit_score(customer)
            interest_rate = self.determine_interest_rate(customer, credit_score)
            
            proposal = {
                "CustomerName": customer['name'],
                "MonthsToPayBackLoan": self.map_data['gameLengthInMonths'],
                "YearlyInterestRate": interest_rate
            }
            game_input["Proposals"].append(proposal)

        # Generate monthly iterations
        for month in range(self.map_data['gameLengthInMonths']):
            month_actions = {}
            for customer in self.map_data['customers']:
                month_actions[customer['name']] = self.generate_award_strategy(
                    customer, 
                    month, 
                    self.map_data['gameLengthInMonths']
                )
            game_input["Iterations"].append(month_actions)

        return game_input

def main():
    loan_manager = LoanManager("Map.json", "Awards.json")
    game_input = loan_manager.generate_game_input()
    
    # Save or send game input
    with open('game_input.json', 'w') as f:
        json.dump(game_input, f, indent=2)

if __name__ == "__main__":
    main()