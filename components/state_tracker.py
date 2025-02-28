import sys
import traceback

from data.database import Database

class StateTracker:
    def __init__(self, database: Database):
        self.current_intent = None
        self.current_slots = {}
        self.next_best_actions = []
        self.database = database
        self.current_houses = []
        self.houses_to_compare = []
        self.properties_to_compare = []
        self.active_house = None

    def update(self, nlu_output):

        if not isinstance(nlu_output, list) or len(nlu_output) == 0:
            self.current_intent = "FALLBACK_POLICY"
            self.current_slots = {"reason": "An error occured, please try again."}
            return

        for chunk in nlu_output:
            intent, slots = chunk['intent'], chunk['slots']

            #! Error handling and fallback policy
            if intent not in ["HOUSE_SEARCH", "HOUSE_SELECTION", "ASK_INFO", "COMPARE_HOUSES", "OUT_OF_DOMAIN"]:
                self.current_intent = "FALLBACK_POLICY"
                self.current_slots = {"reason": "Unknown intent for the current system, please try again."}
                continue
            elif intent == "OUT_OF_DOMAIN":
                self.current_intent = "FALLBACK_POLICY"
                self.current_slots = {"reason": "The intent of the user request is out of the domain of the current system."}
                continue
            
            if not self.current_intent: # Initial state
                self.current_intent = intent
                self.initialize_slots(intent, slots)
            elif intent == self.current_intent: # Same intent
                if intent == "ASK_INFO":
                    self.current_slots = slots
                else:
                    self.current_slots.update((k, v) for k, v in slots.items() if v is not None and v != "None" and v != "null")

                if self.check_slots():
                    self.handle_intent(intent)
            else:
                if not self.check_slots():
                    #TODO Handle this part
                    #! Handle this missing information later with the fallback policy
                    raise Exception("Error: The previous slots are not valid.")
                else:
                    self.current_intent = intent
                    self.current_slots = slots
                    print("*"*100)
                    print(f"Changing intent to {intent} with slots {slots}")
                    print("*"*100)
                    # if self.check_slots():
                    #     self.handle_intent(intent)
                    # else:
                    self.initialize_slots(intent, slots)

    
    def initialize_slots(self, intent, slots):
        """Initialize the slots for the current intent.
        Make sure that all the slots for a given intent are inserted in the current_slots dictionary.
        """
        if intent == "HOUSE_SEARCH":
            self.current_slots = {"house_size": None, "house_bhk": None, "house_rent": None, "house_location": None, "house_city": None, "house_furnished": None}
            for key, value in slots.items():
                if value is not None and value != "None" and value != "null":
                    self.current_slots[key] = value
        elif intent == "HOUSE_SELECTION":
            self.current_slots = {"house_selected": None}
            for key, value in slots.items():
                if value is not None and value != "None" and value != "null":
                    self.current_slots[key] = value
        elif intent == "ASK_INFO":
            #! To test
            if not self.active_house:
                self.current_intent = "FALLBACK_POLICY"
                self.current_slots = {"reason": "No house selected, you must search or select a house first."}
            else:
                self.current_slots = slots
        elif intent == "COMPARE_HOUSES":
            #! To test
            if not self.current_houses:
                self.current_intent = "FALLBACK_POLICY"
                self.current_slots = {"reason": "No houses found to be compared, you must search for houses first."}
            else:
                try:
                    #TODO handle this better
                    self.houses_to_compare = [self.current_houses[idx] for idx in slots["houses"]]
                    self.properties_to_compare = slots['properties']
                    print(f"Comparing houses: {self.houses_to_compare}")
                except Exception as e:
                    print("Error in parsing the compare houses intent", file=sys.stderr)
                    print(traceback.format_exc())
                    self.current_intent = "FALLBACK_POLICY"
                    self.current_slots = {"reason": "Error in processing the user request. Please try again."}
        else:
            raise Exception(f"Error: Initializing slots for an unknown intent {intent}.")
    
    def check_slots(self):
        for val in self.current_slots.values():
            if not val:
                return False
        return True
    
    def update_nba(self, dm_output):
        self.next_best_actions.extend(dm_output)

    def handle_intent(self, intent):
        """Handles one intent, once its slots are filled"""

        if intent == "HOUSE_SEARCH":
            #! To test no houses found
            if "confirmation" in self.next_best_actions[-2] and "HOUSE_SEARCH" in self.next_best_actions[-2]:
                self.current_houses = self.database.get_houses(self.current_slots)
                houses = self.current_houses[:3] if len(self.current_houses) > 3 else self.current_houses
                self.current_intent = "SHOW_HOUSES"
                self.current_slots = {f"option_{i}": str(house) for i, house in enumerate(houses)}
                print("="*100)
                print(f"The search resulted in {len(houses)} houses.")
                print("="*100)
        elif intent == "HOUSE_SELECTION":
            if self.current_slots['house_selected'] is not None:
                try:
                    index = int(self.current_slots['house_selected'])
                    self.active_house = self.current_houses[index-1]
                    print(f"House activated: {self.active_house}")
                    self.current_intent = "ASK_INFO"
                    self.current_slots = {}
                except Exception:
                    print("Error in converting the house index", file=sys.stderr)
                    self.current_intent = "ASK_INFO"
                    self.current_slots = {}
        elif intent == "COMPARE_HOUSES":
            self.properties_to_compare = self.current_slots["properties"]
            if self.houses_to_compare == []:
                try:
                    self.houses_to_compare = [self.current_houses[i] for i in self.current_slots["houses"]]
                    print(f"Comparing houses: {self.houses_to_compare}")
                except Exception:
                    print("Error in parsing the compare houses intent", file=sys.stderr)
                    self.current_intent = "COMPARE_HOUSES"
                    self.current_slots = {}
        elif intent == "ASK_INFO":
            if not self.active_house:
                self.current_intent = "FALLBACK_POLICY"
                self.current_slots = {"reason": "No house selected, you must search or select a house first."}
        else:
            raise Exception(f"StateTracker Error: Handling an unknown intent {intent}.")
        
    def test(self):
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': None, 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Mumbai", 'house_city': "Mumbai", 'house_furnished': "Furnished"}}])
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': "100", 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Nalasopara", 'house_city': "Mumbai", 'house_furnished': "Unfurnished"}}])

    def get_state(self) -> dict:
        info = {"intent": self.current_intent, "slots": self.current_slots}
        return info
    
    def reset(self):
        self.current_intent = None
        self.current_slots = {}
        self.next_best_actions = []
        self.current_houses = []
        self.houses_to_compare = []
        self.properties_to_compare = []
        self.active_house = None