import os

from utils.utils import generate
from .state_tracker import StateTracker

class DM:
    def __init__(self, model, tokenizer, args, verbose=False):  
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.verbose = verbose

    def __call__(self, state_tracker: StateTracker):

        dm_outputs = []

        intent = state_tracker.current_intent
        slots = state_tracker.current_slots
        info = f"Intent: {intent}, Slots: {slots}"
        
        path = os.path.join("prompts", self.args.domain, "dm.txt")
        system_prompt = open(path, "r").read()
        system_prompt = self.args.chat_template.format(system_prompt, info)
        print(f"DM Text: '{system_prompt}'") if self.verbose else None
        dm_output = generate(self.model, system_prompt, self.tokenizer, self.args)
        dm_outputs.append(dm_output)

        self.post_process(dm_outputs)

        return dm_outputs
    
    def post_process(self, dm_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i in range(len(dm_outputs)):
            dm_outputs[i] = dm_outputs[i].strip("\n")
            if len(dm_outputs[i]) == 0:
                to_remove.append(i)
        
        # TODO: Handle this missing information later with the fallback policy
        for i in to_remove:
            dm_outputs.pop(i)

        return dm_outputs
