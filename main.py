import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import json
import codecs
import http.client

class LoanManager:
    def __init__(self, map_data_path="Map-Gothenburg.json", awards_data_path="Awards.json"):
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
        try:
            with codecs.open(file_path, 'r', encoding='utf-8-sig') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: Could not find file {file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in file {file_path}")
            print(f"Details: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error reading {file_path}: {str(e)}")
            raise

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

    def submit_to_api(self, game_input, api_key):
        """Submit game input to the API and get feedback"""
        try:
            conn = http.client.HTTPSConnection("api.considition.com")
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key
            }
            
            conn.request("POST", "/game", json.dumps(game_input), headers)
            response = conn.getresponse()
            result = json.loads(response.read().decode())
            
            conn.close()
            return result
        except Exception as e:
            print(f"API submission error: {str(e)}")
            raise

def test_multiple_variations(api_key, num_variations=5):
    loan_manager = LoanManager()
    best_score = float('-inf')
    best_input = None
    
    for i in range(num_variations):
        game_input = loan_manager.generate_game_input()
        api_response = loan_manager.submit_to_api(game_input, api_key)
        
        if 'score' in api_response and api_response['score'] > best_score:
            best_score = api_response['score']
            best_input = game_input
            
        print(f"Variation {i+1} score: {api_response.get('score', 'N/A')}")
    
    print(f"\nBest score: {best_score}")
    # Save best input
    with open('best_game_input.json', 'w', encoding='utf-8') as f:
        json.dump(best_input, f, indent=2)
    
    return best_input, best_score

def main():
    try:
        # Initialize the loan manager
        loan_manager = LoanManager()
        
        # Generate game input
        game_input = loan_manager.generate_game_input()
        
        # Save game input locally
        with open('game_input.json', 'w', encoding='utf-8') as f:
            json.dump(game_input, f, indent=2)
        print("Successfully generated game input!")
        
        # Submit to API and get feedback
        api_key = "YOUR_API_KEY_