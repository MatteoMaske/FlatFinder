import os

from components.state_tracker import StateTracker
from utils.utils import generate

class NLG:
    def __init__(self, model, tokenizer, args, verbose=False):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.verbose = verbose

    def __call__(self, state_tracker: StateTracker, conversation=[]):

        dm_output = list(state_tracker.next_best_actions[-1])
        intent = state_tracker.current_intent
        slots = state_tracker.current_slots
        info = f"\nIntent: {intent}, Slots: {slots}"

        nlg_outputs = []

        for next_best_action in dm_output:
            path = os.path.join("prompts", self.args.domain, "nlg.txt")
            system_prompt = open(path, "r").read()
            system_prompt = self.args.chat_template.format(system_prompt, next_best_action+info)
            print(f"NLG Text: '{system_prompt}'") if self.verbose else None

            nlg_output = generate(self.model, system_prompt, self.tokenizer, self.args)
            nlg_outputs.append(nlg_output)

        self.post_process(nlg_outputs)

        return nlg_outputs[0]
    
    def post_process(self, nlg_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i in range(len(nlg_outputs)):
            nlg_outputs[i] = nlg_outputs[i].strip("\n")
            if len(nlg_outputs[i]) == 0:
                to_remove.append(i)
        
        # TODO: Handle this missing information later with the fallback policy
        for i in to_remove:
            nlg_outputs.pop(i)

        return nlg_outputs
