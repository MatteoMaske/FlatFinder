import json
import string
import random
import os

from components.nlu import NLU
from components.dm import DM
from tqdm import tqdm

class Evaluator:
    def __init__(self, nlu_test_path=None, dm_test_path=None):
        if nlu_test_path:
            test_file = open(nlu_test_path)
            self.nlu_data = json.load(test_file)
        
        if dm_test_path:
            test_file = open(dm_test_path)
            self.dm_data = json.load(test_file)

    def create_test_set(self, cached=True):
        """Create a test set for the NLU model and save it for later reproducibility"""
        if cached and os.path.exists("test/house_agency/test_set.json"):
            with open("test/house_agency/test_set.json") as f:
                test_set = json.load(f)
            return test_set

        test_set = []
        for object in self.nlu_data:
            intent = object["intent"]
            templates = object["templates"]
            for template in templates:
                user_input, values = self.generate_random_sample(template)
                ground_truth = self.generate_gt(intent, values)
                
                test_set.append({
                    "user_input": user_input,
                    "ground_truth": ground_truth
                })

        # Save the test set
        test_set_path = os.path.join("test", "house_agency", "test_set.json")
        with open(test_set_path, "w") as f:
            json.dump(test_set, f, indent=4)


        return test_set

    def generate_random_sample(self, template)-> tuple[str,dict]:
        """Given a certain template, generate a random user input based on the template
        
        Args:
            template (str): A template string

        Returns:
            user_input (str): A user input generated from the template
            random_values (dict): A dictionary containing the random values used to generate the user input
        """
        keys = [t[1] for t in string.Formatter.parse("", template)]

        random_values = {}
        for key in keys:
            if key is None:
                continue
            if key == "house_bhk":
                random_values[key] = str(random.randint(1,6))
            elif key == "house_size":
                random_values[key] = str(random.choice(range(500, 3000, 100)))
            elif key == "house_rent":
                random_values[key] = str(random.choice(range(2000, 100000, 1000)))
            elif key == "house_location":
                random_values[key] = random.choice(['Narayanapura', 'Aarna Enclave', 'Abbigere', 'Adugodi', 'Agrahara Layout',
                                                'Colony-Velachery', 'Adambakkam', 'Adyar', 'Alandur', 'Thiruvanmiyur',
                                                'Abiramapuram', 'Sardar Patel Road', 'Konnur Highroad', 'Hebbal', 'Singasandra',
                                                'Mahadevapura', 'Kaggadasapura', 'Vidyaranyapura', 'Hosur Road', 'Ayanavaram'])
            elif key == "house_city":
                random_values[key] = random.choice(['Kolkata', 'Mumbai', 'Bangalore', 'Delhi', 'Chennai', 'Hyderabad'])
            elif key == "house_furnished":
                random_values[key] = random.choice(['furnished', 'unfurnished', 'semi-furnished'])
            elif "info_type" in key or "property" in key:
                random_values[key] = random.choice(['price', 'location', 'size', 'bhk', 'number of bathrooms', 'tenant preferred by the landlord', 'landlord contact', 'floors in the building'])
            elif "house_index" in key or "house_selected" in key:
                random_values[key] = random.choice(['1', '2', '3', '4', '5', 'one', 'two', 'three', 'four', 'five'])

        user_input = template.format(**random_values)
        return user_input, random_values
    
    def generate_gt(self, intent, values):
        """Given the values to generate the user input, generate the ground truth for the intent
        
        Args:
            intent (str): The intent of the user input
            values (dict): The values used to generate the user input
            
        Returns:
            ground_truth (dict): The ground truth for the intent and for the slot values        
        """

        ground_truth = {
            "intent": intent,
            "slots": {}
        }

        if intent == "HOUSE_SELECTION":
            for key, value in values.items():
                if value.isdigit():
                    ground_truth["slots"][key] = int(value)
                else:
                    match value:
                        case "one":
                            ground_truth["slots"][key] = 1
                        case "two":
                            ground_truth["slots"][key] = 2
                        case "three":
                            ground_truth["slots"][key] = 3
                        case "four":
                            ground_truth["slots"][key] = 4
                        case "five":
                            ground_truth["slots"][key] = 5
                        case _:
                            raise ValueError(f"Invalid value {value} for key {key}")
        elif intent == "ASK_INFO":
            ground_truth["slots"]["properties"] = []
            for key, value in values.items():
                ground_truth["slots"]["properties"].append(value)
        elif intent == "COMPARE_HOUSES":
            ground_truth["slots"]["properties"] = []
            ground_truth["slots"]["houses"] = []
            
            for key, value in values.items():
                if "house" in key:
                    if value.isdigit():
                        ground_truth["slots"]["houses"].append(int(value)-1)
                    else:   
                        match value:
                            case "one":
                                ground_truth["slots"]["houses"].append(0)
                            case "two":
                                ground_truth["slots"]["houses"].append(1)
                            case "three":
                                ground_truth["slots"]["houses"].append(2)
                            case "four":
                                ground_truth["slots"]["houses"].append(3)
                            case "five":
                                ground_truth["slots"]["houses"].append(4)
                            case _:
                                raise ValueError(f"Invalid value {value} for key {key}")
                else:
                    ground_truth["slots"]["properties"].append(value)
        else:
            for key, value in values.items():
                ground_truth["slots"][key] = value

        return ground_truth


    def calculate_accuracy_f1(self, nlu_output, ground_truth):
        """Calculate the accuracy and F1 score for the NLU output
        
        Args:
            nlu_output (dict): The NLU output
            ground_truth (dict): The ground truth
            
        Returns:
            result (dict): A dictionary containing accuracy, precision, recall and F1 score
        """
        result = {}
        result["accuracy"] = nlu_output["intent"] == ground_truth["intent"]

        # Calculate the F1 score
        nlu_slots = nlu_output["slots"]
        gt_slots = ground_truth["slots"]
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for key, value in gt_slots.items():
            if key in nlu_slots:
                if nlu_slots[key] == value:
                    true_positives += 1
                else:
                    false_negatives += 1
            else:
                false_negatives += 1

        for key, value in nlu_slots.items():
            if key not in gt_slots:
                false_positives += 1

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        # F1 score is the harmonic mean of precision and recall
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        result["precision"] = precision
        result["recall"] = recall
        result["f1"] = f1

        return result

    # TODO: Check the how history is built and recall value
    def evaluate_NLU(self, nlu_model, conversation):
        test_set = self.create_test_set(cached=False)
        metrics = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
        }

        loop = tqdm(test_set, desc="Evaluating NLU", total=len(test_set), colour="green")
        for sample in loop:
            conversation.reset(_for=sample["ground_truth"]["intent"])

            user_input = sample["user_input"]
            ground_truth = sample["ground_truth"]
            nlu_output = nlu_model(user_input, conversation.get_history())
            nlu_output = nlu_output[0] if len(nlu_output) > 0 else {"intent": None, "slots": {} }

            result = self.calculate_accuracy_f1(nlu_output, ground_truth)
            metrics["accuracy"] += result["accuracy"]
            metrics["precision"] += result["precision"]
            metrics["recall"] += result["recall"]
            metrics["f1"] += result["f1"]

            if result["accuracy"] == 0:
                print("Sample failed")
                print(f"User input: {user_input}")
                print(f"NLU output: {nlu_output}")
                print(f"Ground truth: {ground_truth}")


        num_samples = len(test_set)
        metrics["accuracy"] /= num_samples
        metrics["precision"] /= num_samples
        metrics["recall"] /= num_samples
        metrics["f1"] /= num_samples

        return metrics
        
    def evaluate_DM(self, nlg_model):
        pass