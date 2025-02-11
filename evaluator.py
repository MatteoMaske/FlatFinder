import json
import string

from components.nlu import NLU
from components.dm import DM
import random

class Evaluator:
    def __init__(self, nlu_test_path: str = None, dm_test_path: str = None):
        if nlu_test_path:
            test_file = open(nlu_test_path)
            self.nlu_data = json.load(test_file)
        
        if dm_test_path:
            test_file = open(dm_test_path)
            self.dm_data = json.load(test_file)

    def create_test_set(self):
        test_set = []
        for object in self.nlu_data:
            intent = object["intent"]
            templates = object["templates"]
            for template in templates:
                user_input, ground_truth = self.generate_random_sample(template)
                test_set.append({
                    "intent": intent,
                    "user_input": user_input,
                    "ground_truth": ground_truth
                })
        return test_set

    def generate_random_sample(self, template):
        keys = [t[1] for t in string.Formatter.parse("",template)]

        random_values = {}
        for key in keys:
            if key == "house_bhk":
                random_values[key] = str(random.randint(1,6))
            elif key == "house_size":
                random_values[key] = str(random.randint(500, 3000))
            elif key == "house_rent":
                random_values[key] = str(random.randint(2000, 100000))
            elif key == "house_location":
                random_values[key] = random.choice(['Narayanapura', 'Aarna Enclave', 'Abbigere', 'Adugodi', 'Agrahara Layout',
                                                'Colony-Velachery', 'Adambakkam', 'Adyar', 'Alandur', 'Thiruvanmiyur',
                                                'Abiramapuram', 'Sardar Patel Road', 'Konnur Highroad', 'Hebbal', 'Singasandra',
                                                'Mahadevapura', 'Kaggadasapura', 'Vidyaranyapura', 'Hosur Road', 'Ayanavaram'])
            elif key == "house_city":
                random_values[key] = random.choice(['Kolkata' 'Mumbai' 'Bangalore' 'Delhi' 'Chennai' 'Hyderabad'])
            elif key == "house_furnished":
                random_values[key] = random.choice(['furnished', 'unfurnished', 'semi-furnished'])
            elif "info_type" in key:
                random_values[key] = random.choice(['price', 'location', 'size', 'bhk', 'bathrooms', 'balcony', 'bathrooms number', 'tenant preferred', 'contact info', 'floor info'])
            elif "house_index" in key:
                random_values[key] = str(random.randint(1, 10))
            elif "house_selected" in key:
                random_values[key] = random.choice(['1', '2', '3', '4', '5', 'first', 'second', 'third', 'fourth', 'fifth', 'one', 'two', 'three', 'four', 'five'])
            elif "property" in key:
                random_values[key] = random.choice(['price', 'location', 'size', 'bhk', 'bathrooms', 'balcony'])
        return random_values

    def evaluate_NLU(self, nlu_model):
        self.create_test_set()
        nlu_output = nlu_model(user_input, conversation.get_history(until=-1))

        pass

    def evaluate_DM(self, nlg_model):
        pass
