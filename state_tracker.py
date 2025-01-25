class StateTracker:
    def __init__(self, database=None):
        self.database = database
        self.current_intent = None
        self.current_slots = {}
        self.next_best_actions = []
        self.slots_to_ask = []

    def update(self, nlu_output):

        for chunk in nlu_output:
            intent, slots = chunk['intent'], chunk['slots']

            if not self.current_intent: # Initial state
                self.current_intent = intent
                self.current_slots = slots
            elif intent == self.current_intent: # Same intent
                self.current_slots.update((k, v) for k, v in slots.items() if v is not None)
            else: # Different intent
                if not self.check_slots():
                    #! Handle this missing information later with the fallback policy
                    raise Exception("Error: The previous slots are not valid.")
                else:
                    self.current_intent = intent
                    self.current_slots = slots

    def check_slots(self):
        for val in self.current_slots.values():
            if not val:
                return False
        return True
    
    def update_nba(self, dm_output):
        self.next_best_actions.append(dm_output)