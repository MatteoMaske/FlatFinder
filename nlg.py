import json
from utils import generate, PROMPTS

class NLG:
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def __call__(self, dm_output):

        nlg_outputs = []

        for next_best_action in dm_output:
            nlg_text = self.args.chat_template.format(PROMPTS[self.args.domain]["NLG"], next_best_action)
            nlg_output = generate(self.model, nlg_text, self.tokenizer, self.args)
            nlg_outputs.append(nlg_output)

        self.post_process(nlg_outputs)

        return nlg_outputs
    
    def post_process(self, nlg_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i, nlg_output in enumerate(nlg_outputs):
            nlg_output = nlg_output.strip()
            if len(nlg_output) == 0:
                to_remove.append(i)
        
        # TODO: Handle this missing information later with the fallback policy
        for i in to_remove:
            nlg_outputs.pop(i)

        return nlg_outputs
