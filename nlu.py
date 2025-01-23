import json
from utils import generate, PROMPTS

class NLU:
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def generate_chunks(self, user_input):
        nlu_text = self.args.chat_template.format(PROMPTS[self.args.domain]["NLU"]["CHUNKING"], user_input)
        nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
        nlu_output = nlu_output.strip()

        try:
            chunks = json.loads(nlu_output)
        except Exception as e:
            print("Error: The NLU output [CHUNKING] is not in the expected json format.")
            print(f"'{nlu_output}'")
            raise e
        
        return chunks
    
    def classify_intent(self, user_input, conversation):
        prompt = PROMPTS[self.args.domain]["NLU"]["INTENT"].format(str(conversation))
        nlu_text = self.args.chat_template.format(prompt, user_input)
        nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
        nlu_output = nlu_output.strip("\n").strip()
        print(f"NLU Intent: '{nlu_output}'")

        return [{"intent": nlu_output, "chunk": user_input}]

    def __call__(self, user_input, conversation=[], chunks=False):
        
        if chunks:
            chunks = self.generate_chunks(user_input)
            print(f"NLU Chunks found: {chunks}")
        else:
            chunks = self.classify_intent(user_input, conversation)

        nlu_outputs = []

        for chunk in chunks:
            intent = chunk['intent'].upper()
            if intent not in PROMPTS[self.args.domain]['NLU'].keys():
                print(f"Error: The detected intent {intent} is not in the domain {self.args.domain}.")
                continue
            nlu_text = self.args.chat_template.format(PROMPTS[self.args.domain]["NLU"][intent], chunk['chunk'])
            nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
            nlu_outputs.append((intent, nlu_output))

        self.post_process(nlu_outputs)

        return nlu_outputs
    
    def post_process(self, nlu_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i, (intent, nlu_output) in enumerate(nlu_outputs):
            try:
                nlu_output_dict = json.loads(nlu_output)
                nlu_outputs[i] = {"intent": intent, "slots": nlu_output_dict}
            except Exception as e:
                print(f"Error: The NLU output '{nlu_output}' is not in the expected json format.")
                to_remove.append(i)
        
        # TODO: Handle this missing information later with the fallback policy
        for i in to_remove:
            nlu_outputs.pop(i)

        return nlu_outputs
