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

    def create_test_set(self, n_sample=3, cached=True):
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
                for _ in range(n_sample):
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

        indices_set = set(range(1,6))
        properties_set = set(['price', 'location', 'size', 'bhk', 'number of bathrooms', 'tenant preferred by the landlord', 'point of contact', 'floors in the building'])
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
                random_values[key] = random.choice(list(properties_set))
                properties_set.remove(random_values[key])
            elif "house_index" in key or "house_selected" in key:
                random_values[key] = str(random.choice(list(indices_set)))
                indices_set.remove(int(random_values[key]))


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
    
    def compute_stats(self, y_true, y_pred):
        """Compute the statistics for the NLU model
        
        Args:
            y_true (list): The ground truth
            y_pred (list): The NLU output
            
        Returns:
            None
        """
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            classification_report
        )
        import seaborn as sns
        import matplotlib.pyplot as plt

        # Simulated ground truth and predictions (3 intents)
        y_true = []
        y_true.extend(('HOUSE_SEARCH,'*3).split(",")[:-1])
        y_true.extend(('HOUSE_SELECTION,'*3).split(",")[:-1])
        y_true.extend(('ASK_INFO,'*3).split(",")[:-1])
        y_true.extend(('COMPARE_HOUSES,'*3).split(",")[:-1])
        y_true.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])

        y_pred = []
        y_pred.extend(('HOUSE_SEARCH,'*2).split(",")[:-1])
        y_pred.append('HOUSE_SELECTION')
        y_pred.extend(('HOUSE_SELECTION,'*3).split(",")[:-1])
        y_pred.extend(('ASK_INFO,'*2).split(",")[:-1])
        y_pred.append('COMPARE_HOUSES')
        y_pred.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])
        y_pred.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])



        # Accuracy
        accuracy = accuracy_score(y_true, y_pred)
        print(f"Accuracy: {accuracy:.2f}")

        # Macro Precision, Recall, F1
        precision = precision_score(y_true, y_pred, average='macro')
        recall = recall_score(y_true, y_pred, average='macro')
        f1 = f1_score(y_true, y_pred, average='macro')

        print(f"Macro Precision: {precision:.2f}")
        print(f"Macro Recall:    {recall:.2f}")
        print(f"Macro F1-score:  {f1:.2f}")

        # Full classification report (per-intent)
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred))

        # Confusion Matrix
        labels = sorted(set(y_true))  # ensure consistent order
        cm = confusion_matrix(y_true, y_pred, labels=labels)

        # Plot confusion matrix
        sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap='Blues')
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.title("Confusion Matrix")
        plt.savefig("confusion_matrix.png")

    # TODO: Check the how history is built and recall value
    def evaluate_NLU(self, nlu_model, conversation):
        test_set = self.create_test_set(cached=False)
        intent_gt = []
        intent_pred = []

        loop = tqdm(enumerate(test_set), desc="Evaluating NLU", total=len(test_set), colour="green")
        for i, sample in loop:
            conversation.reset(_for=sample["ground_truth"]["intent"])

            user_input = sample["user_input"]
            ground_truth = sample["ground_truth"]
            nlu_output = nlu_model(user_input, conversation.get_history())

            intent_gt.append(ground_truth["intent"])
            if len(nlu_output) > 0:
                nlu_output = nlu_output[0]
                intent_pred.append(nlu_output["intent"])
            else:
                intent_pred.append("ERROR")

            if ground_truth["intent"] != nlu_output["intent"]:
                print("Accuracy 0 on this sample ================")
                print(f"Input query: ++++++++++++++\nHistory:\n{conversation.get_history()}\n\nUser: {user_input}\n+++++++++++++++")
                print(f"NLU output: {nlu_output}")
                print(f"Ground truth: {ground_truth}")
                print("===========================================")

        self.compute_stats(intent_gt, intent_pred)
        
    def evaluate_DM(self, nlg_model):
        pass