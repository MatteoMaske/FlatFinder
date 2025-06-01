import json
import random
import os

from string import Formatter
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

        test_set = {"nlu_data": [], "dm_data": []}
        for object in self.nlu_data:
            intent = object["intent"]
            templates = object["templates"]
            for template in templates:
                for _ in range(n_sample):
                    user_input, values = self.generate_nlu_sample(template)
                    ground_truth = self.generate_nlu_gt(intent, values)
                    
                    test_set["nlu_data"].append({
                        "user_input": user_input,
                        "ground_truth": ground_truth
                    })

        for object in self.dm_data:
            intent = object["intent"]
            templates = object["templates"]
            for template in templates:
                ground_truth = self.generate_dm_gt(template)
                test_set["dm_data"].append({
                    "nlu_output": template,
                    "ground_truth": ground_truth
                })

        # Save the test set
        test_set_path = os.path.join("test", "house_agency", "test_set.json")
        with open(test_set_path, "w") as f:
            json.dump(test_set, f, indent=4)


        return test_set

    def generate_nlu_sample(self, template)-> tuple[str,dict]:
        """Given a certain NLU template, generate a random user input based on the template
        
        Args:
            template (str): A template string

        Returns:
            user_input (str): A user input generated from the template
            random_values (dict): A dictionary containing the random values used to generate the user input
        """
        keys = [t[1] for t in Formatter().parse(template) if t[1] is not None]

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
    
    def generate_nlu_gt(self, intent, values):
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
                    ground_truth["slots"][key] = int(value)-1
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
                    if "bathrooms" in value:
                        ground_truth["slots"]["properties"].append("bathrooms")
                    elif "floors" in value:
                        ground_truth["slots"]["properties"].append("floors")
                    ground_truth["slots"]["properties"].append(value)

            # Set values as None (json null) if they are empty
            if not ground_truth["slots"]["houses"]:
                ground_truth["slots"]["houses"] = None
            if not ground_truth["slots"]["properties"]:
                ground_truth["slots"]["properties"] = None
        else:
            for key, value in values.items():
                ground_truth["slots"][key] = value

        return ground_truth

    
    
    def generate_dm_gt(self, nlu_output)-> str:
        """Given a certain DM template, generate a random user input based on the template
        
        Args:
            template (dict): A template of a NLU output

        Returns:
            user_input (str): A user input generated from the template
            random_values (dict): A dictionary containing the random values used to generate the user input
        """
        intent = nlu_output["intent"]
        slots = nlu_output["slots"]
        ground_truth = ""

        missing_slot = [key for key, value in slots.items() if value is None]
        if len(missing_slot) > 0:
            ground_truth = "request_slot"
        elif intent != "ASK_INFO":
            ground_truth = "confirmation"
        else:
            ground_truth = "provide_info"

        return ground_truth

        
    def compute_stats(self, y_true, y_pred, task_type='intent', fuzz_th=80):
        """
        Evaluate NLU predictions for either intent classification or slot filling.
        
        Args:
            y_true (list): Ground truth values
            y_pred (list): Predicted values
            task_type (str): 'intent' or 'slots'
            fuzz_th (int): Fuzzy matching threshold (used only for slots)
        
        Returns:
            tuple or None: Precision, Recall, F1 (only returned for 'slots' mode)
        """
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            classification_report
        )
        import matplotlib.pyplot as plt
        import seaborn as sns

        if task_type == 'intent':
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, average='macro')
            recall = recall_score(y_true, y_pred, average='macro')
            f1 = f1_score(y_true, y_pred, average='macro')

            print(f"Accuracy:        {accuracy:.2f}")
            print(f"Macro Precision: {precision:.2f}")
            print(f"Macro Recall:    {recall:.2f}")
            print(f"Macro F1-score:  {f1:.2f}")

            print("\nClassification Report:")
            print(classification_report(y_true, y_pred))

            labels = sorted(set(y_true))
            cm = confusion_matrix(y_true, y_pred, labels=labels)

            plt.figure(figsize=(12, 10))
            sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap='Blues', cbar=False)
            plt.xlabel("Predicted", fontsize=12)
            plt.xticks(rotation=15, ha='right', fontsize=10)
            plt.ylabel("True", fontsize=12)
            plt.yticks(fontsize=10)
            plt.title("Confusion Matrix", fontsize=14)
            plt.savefig("test/house_agency/intent_confusion_matrix.png", bbox_inches='tight')
            plt.show()

        elif task_type == 'slots':
            from fuzzywuzzy import fuzz

            fuzz_decisions = [
                fuzz.ratio(t.lower(), p.lower()) >= fuzz_th
                for t, p in zip(y_true, y_pred)
            ]
            
            # for i, decision in enumerate(fuzz_decisions):
            #     if not decision:
            #         print(f"Fuzzy match failed for index {i}: True='{y_true[i]}', Predicted='{y_pred[i]}'")

            y_pred = [y_true[i] if fuzz_decisions[i] else y_pred[i] for i in range(len(y_pred))]

            precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
            recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
            f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)

            print(f"Slots Precision: {precision:.2f}")
            print(f"Slots Recall:    {recall:.2f}")
            print(f"Slots F1-score:  {f1:.2f}")

            return precision, recall, f1

        else:
            raise ValueError("task_type must be either 'intent' or 'slots'")

    def evaluate_NLU(self, nlu_model, conversation):

        test_set = self.create_test_set(cached=False)["nlu_data"]
        intent_gt = []
        intent_pred = []
        slot_gt = []
        slot_pred = []
        results = []

        loop = tqdm(enumerate(test_set), desc="Evaluating NLU", total=len(test_set), colour="green")
        for i, sample in loop:
            conversation.reset(_for=sample["ground_truth"]["intent"])

            user_input = sample["user_input"]
            ground_truth = sample["ground_truth"]
            nlu_output = nlu_model(user_input, conversation.get_history())
            results.append({
                "sample": sample,
                "nlu_output": nlu_output
            })

            intent_gt.append(ground_truth["intent"])
            if len(nlu_output) > 0:
                nlu_output = nlu_output[0]
                intent_pred.append(nlu_output["intent"])
                if ground_truth["intent"] != nlu_output["intent"]:
                    print("Accuracy 0 on this sample ================")
                    print(f"Input query: ++++++++++++++\nHistory:\n{conversation.get_history()}\n\nUser: {user_input}\n+++++++++++++++")
                    print(f"NLU output: {nlu_output}")
                    print(f"Ground truth: {ground_truth}")
                    print("===========================================")
                
                true_slots = ground_truth.get('slots', {})
                pred_slots = nlu_output.get('slots', {})
                common_keys = set(true_slots.keys()) & set(pred_slots.keys())

                for key in common_keys:
                    slot_gt.append(str(true_slots[key]))
                    slot_pred.append(str(pred_slots[key]))
            else:
                intent_pred.append("ERROR")
                print("NLU output is empty")

        # Save results
        json.dump(results, open("test/house_agency/nlu_results.json", "w"), indent=4)

        self.compute_stats(intent_gt, intent_pred, task_type="intent")
        self.compute_stats(slot_gt, slot_pred, task_type="slots")

    
    def evaluate_NLU_fake(self):
        intent_gt = []
        intent_pred = []
        slots = {}
        results = json.load(open("test/house_agency/nlu_results.json"))

        loop = tqdm(enumerate(results), desc="Evaluating NLU", total=len(results), colour="green")
        for i, test in loop:
            ground_truth = test["sample"]["ground_truth"]
            nlu_output = test["nlu_output"]
            intent_gt.append(ground_truth["intent"])
            if ground_truth["intent"] not in slots:
                slots[ground_truth["intent"]] = {"gt": [], "pred": []}

            if len(nlu_output) > 0:
                nlu_output = nlu_output[0]
                intent_pred.append(nlu_output["intent"])
                
                true_slots = ground_truth.get('slots', {})
                pred_slots = nlu_output.get('slots', {})
                common_keys = set(true_slots.keys()) & set(pred_slots.keys())

                for key in common_keys:
                    slots[ground_truth["intent"]]["gt"].append(str(true_slots[key]))
                    slots[ground_truth["intent"]]["pred"].append(str(pred_slots[key]))
                    if true_slots[key] != pred_slots[key]:
                        print(f"Slots mismatch: {key} - gt: {true_slots[key]}, Predicted: {pred_slots[key]}")
            else:
                intent_pred.append("ERROR")
                print("NLU output is empty")

        self.compute_stats(intent_gt, intent_pred, task_type="intent")
        for intent, slot_data in slots.items():
            slot_gt = slot_data["gt"]
            slot_pred = slot_data["pred"]
            print(f"Evaluating slots for intent: {intent}")
            self.compute_stats(slot_gt, slot_pred, task_type="slots")

    def evaluate_DM(self, nlg_model):
        test_set = self.create_test_set(cached=True)["dm_data"]

if __name__ == "__main__":
    evaluator = Evaluator(nlu_test_path="test/house_agency/nlu.json", dm_test_path="test/house_agency/dm.json")
    evaluator.evaluate_NLU_fake()