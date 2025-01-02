import argparse
from argparse import Namespace

import torch, json, ollama

from utils import load_model, generate, MODELS, TEMPLATES, PROMPTS


def get_args() -> Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m query_model",
        description="Query a specific model with a given input.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "model_name",
        type=str,
        choices=list(MODELS.keys()),
        help="The model to query.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="The device to use for the model.",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Split the model across multiple devices.",
    )
    parser.add_argument(
        "--dtype",
        type=str,
        choices=["f32", "bf16"],
        default="bf16",
        help="The data type to use for the model.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=128,
        help="The maximum sequence length to use for the model.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=PROMPTS.keys(),
        default="HOUSE_AGENCY",
        help="The domain to use for the model."
    )

    parsed_args = parser.parse_args()
    parsed_args.chat_template = TEMPLATES[parsed_args.model_name]
    parsed_args.model_name = MODELS[parsed_args.model_name]

    return parsed_args

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
            print("Error: The NLU output [CHUNKING] is not in the expected python list format.")
            raise e
        
        return chunks

    def __call__(self, user_input):

        chunks = self.generate_chunks(user_input)
        print(f"NLU Chunks found: {chunks}")
        nlu_outputs = []

        for chunk in chunks:
            intent = chunk['intent'].upper()
            if intent not in PROMPTS[self.args.domain]['NLU'].keys():
                print(f"Error: The detected intent {intent} is not in the domain {self.args.domain}.")
                continue
            nlu_text = self.args.chat_template.format(PROMPTS[self.args.domain]["NLU"][intent], chunk['chunk'])
            nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
            nlu_outputs.append(nlu_output)

        self.post_process(nlu_outputs)

        return nlu_outputs
    
    def post_process(self, nlu_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i, nlu_output in enumerate(nlu_outputs):
            try:
                nlu_outputs[i] = json.loads(nlu_output)
            except Exception as e:
                print(f"Error: The NLU output {nlu_output} is not in the expected json format.")
                to_remove.append(i)
        
        # TODO: Handle this missing information later with the fallback policy
        for i in to_remove:
            nlu_outputs.pop(i)

        return nlu_outputs

def main():
    args = get_args()
    if args.model_name != "llama3:latest":
        model, tokenizer = load_model(args)
    else:
        ollama.show(args.model_name)
        model, tokenizer = None, None

    while True:
        user_input = input("User: ")

        # get the NLU output
        nlu_component = NLU(model, tokenizer, args)
        nlu_output = nlu_component(user_input)
        print(f"NLU: {nlu_output}")

        # Optional Pre-Processing for DM
        # nlu_output = nlu_output.strip()

        # # get the DM output
        # dm_text = args.chat_template.format(PROMPTS["DM"], nlu_output)
        # dm_input = tokenizer(dm_text, return_tensors="pt").to(model.device)
        # dm_output = generate(model, dm_input, tokenizer, args)
        # print(f"DM: {dm_output}")

        # # Optional Pre-Processing for NLG
        # dm_output = dm_output.strip()

        # # get the NLG output
        # nlg_text = args.chat_template.format(PROMPTS["NLG"], dm_output)
        # nlg_input = tokenizer(nlg_text, return_tensors="pt").to(model.device)
        # nlg_output = generate(model, nlg_input, tokenizer, args)

        # print(f"NLG: {nlg_output}")


if __name__ == "__main__":
    main()
