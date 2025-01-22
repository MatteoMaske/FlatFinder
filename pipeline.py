import argparse
from argparse import Namespace

import torch, json, ollama

from utils import load_model, generate, MODELS, TEMPLATES, PROMPTS
from nlu import NLU
from dm import DM
from nlg import NLG


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
        default=1000,
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

        # get the DM output
        dm_component = DM(model, tokenizer, args)
        dm_output = dm_component(nlu_output)
        print(f"DM: {dm_output}")

        # get the NLG output
        nlg_component = NLG(model, tokenizer, args)
        nlg_output = nlg_component(dm_output)
        print(f"NLG: {nlg_output}")


if __name__ == "__main__":
    main()
