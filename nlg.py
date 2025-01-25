import json
from utils import generate, PROMPTS

class NLG:
    def __init__(self, model, tokenizer, args, verbose=False):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.verbose = verbose

    def __call__(self, dm_output, conversation=[]):

        nlg_outputs = []

        for next_best_action in dm_output:
            prompt = PROMPTS[self.args.domain]["NLG"].format(conversation)
            nlg_text = self.args.chat_template.format(prompt, next_best_action)
            print(f"NLG Text: '{nlg_text}'") if self.verbose else None
            nlg_output = generate(self.model, nlg_text, self.tokenizer, self.args)
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
