import os, json
from utils.utils import generate
from prompts.house_agency.nlu_prompts import NLU_PROMPTS

class NLU:
    def __init__(self, model, tokenizer, args, verbose=False):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.verbose = verbose

    def generate_chunks(self, user_input):
        nlu_text = self.args.chat_template.format(NLU_PROMPTS[self.args.domain]["NLU"]["CHUNKING"], user_input)
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
        path = os.path.join("prompts", self.args.domain, "intent.txt")
        system_prompt = open(path, "r").read()
        system_prompt = system_prompt.format(conversation)
        print(f"NLU [Intent] Prompt: '{system_prompt}'") if self.verbose else None

        nlu_text = self.args.chat_template.format(system_prompt, user_input)
        nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
        nlu_output = nlu_output.strip("\n").strip()
        print(f"NLU Intent: '{nlu_output}'") if self.verbose else None

        if "OUT_OF_DOMAIN" in nlu_output:
            print("OUT_OF_DOMAIN detected.")

        return [{"intent": nlu_output, "chunk": user_input}]

    def __call__(self, user_input, conversation=[], chunks=False):
        
        if chunks:
            chunks = self.generate_chunks(user_input)
            print(f"NLU Chunks found: {chunks}")
        else:
            chunks = self.classify_intent(user_input, conversation)
        print(f"NLU Chunks: {chunks}") if self.verbose else None
        
        nlu_outputs = []

        for chunk in chunks:
            intent = chunk['intent'].upper()
            user_input = chunk['chunk']
            if intent not in NLU_PROMPTS.keys():
                nlu_outputs.append(("OUT_OF_DOMAIN", {} ))
                continue
            system_prompt = NLU_PROMPTS[intent].format(conversation)
            system_prompt = self.args.chat_template.format(system_prompt, user_input)
            print(f"NLU [Slots] prompt: '{system_prompt}'") if self.verbose else None
            nlu_output = generate(self.model, system_prompt, self.tokenizer, self.args)
            nlu_outputs.append((intent, nlu_output))

        self.post_process(nlu_outputs)

        return nlu_outputs
    
    def post_process(self, nlu_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i, (intent, nlu_output) in enumerate(nlu_outputs):
            if nlu_output == {}:
                continue
            try:
                if "{" in nlu_output and "}" in nlu_output:
                    nlu_output = nlu_output[nlu_output.index("{") : nlu_output.index("}")+1]
                nlu_output_dict = json.loads(nlu_output)
                nlu_outputs[i] = {"intent": intent, "slots": nlu_output_dict}
            except Exception as e:
                print(f"Error: The NLU output '{nlu_output}' is not in the expected json format.")
                to_remove.append(i)
        
        for i in to_remove:
            nlu_outputs.pop(i)

        return nlu_outputs