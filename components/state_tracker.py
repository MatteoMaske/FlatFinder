import pandas as pd
import sys

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

        for chunk in nlu_output:
            intent, slots = chunk['intent'], chunk['slots']

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
                    #! Handle this missing information later with the fallback policy
                    raise Exception("Error: The previous slots are not valid.")
                else:
                    self.current_intent = intent
                    self.current_slots = slots
                    print("*"*100)
                    print(f"Changing intent to {intent} with slots {slots}")
                    print("*"*100)
                    if self.check_slots():
                        self.handle_intent(intent)
                    else:
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
            self.current_slots = slots
        elif intent == "COMPARE_HOUSES":
            try:
                self.houses_to_compare = [self.current_houses[slots["houses"]]]
                self.properties_to_compare = slots['properties']
            except Exception:
                print("Error in parsing the compare houses intent", file=sys.stderr)
                self.current_intent = "COMPARE_HOUSES"
                self.current_slots = {}
    
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
            if "confirmation" in self.next_best_actions[-1] and "HOUSE_SEARCH" in self.next_best_actions[-1]:
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
                except Exception:
                    print("Error in parsing the compare houses intent", file=sys.stderr)
                    self.current_intent = "COMPARE_HOUSES"
                    self.current_slots = {}
        
    def test(self):
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': None, 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Mumbai", 'house_city': "Mumbai", 'house_furnished': "Furnished"}}])
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': "100", 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Nalasopara", 'house_city': "Mumbai", 'house_furnished': "Unfurnished"}}])

    def get_state(self) -> dict:
        info = {"intent": self.current_intent, "slots": self.current_slots}
        return info