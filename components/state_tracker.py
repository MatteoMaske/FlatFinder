import pandas as pd
import sys

from data.database import Database

class StateTracker:
    def __init__(self, database: Database):
        self.current_intent = None
        self.current_slots = {}
        self.next_best_actions = []
        self.slots_to_ask = []
        self.database = database

    def update(self, nlu_output):

        for chunk in nlu_output:
            intent, slots = chunk['intent'], chunk['slots']

            if not self.current_intent: # Initial state
                self.current_intent = intent
                self.current_slots = slots
            elif intent == self.current_intent: # Same intent
                self.current_slots.update((k, v) for k, v in slots.items() if v is not None and v != "None" and v != "null")
                if self.check_slots():
                    self.handle_intent(intent)
            else: # Different intent
                if not self.check_slots():
                    #! Handle this missing information later with the fallback policy
                    raise Exception("Error: The previous slots are not valid.")
                else:
                    self.current_intent = intent
                    self.current_slots = slots
                    print(f"Current intent: {self.current_intent}, Current slots: {self.current_slots}", file=sys.stderr)

    def check_slots(self):
        for val in self.current_slots.values():
            if not val:
                return False
        return True
    
    def update_nba(self, dm_output):
        self.next_best_actions.append(dm_output)

    def handle_intent(self, intent):
        if intent.lower() == "house_search":
            houses = self.database.get_houses(self.current_slots)
            self.current_intent = "show_houses"
            self.current_slots = {}
            print(houses)


    def test(self):
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': None, 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Mumbai", 'house_city': "Mumbai", 'house_furnished': "Furnished"}}])
        self.update([{'intent': 'HOUSE_SEARCH', 'slots': {'house_size': "100", 'house_bhk': "2", 'house_rent': "10000", 'house_location': "Nalasopara", 'house_city': "Mumbai", 'house_furnished': "Unfurnished"}}])

    