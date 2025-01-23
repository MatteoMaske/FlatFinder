import json
from utils import generate, PROMPTS

class DM:
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def __call__(self, nlu_output):

        dm_outputs = []

        for chunk in nlu_output:
            dm_text = self.args.chat_template.format(PROMPTS[self.args.domain]["DM"], str(chunk))
            dm_output = generate(self.model, dm_text, self.tokenizer, self.args)
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
