import argparse
from argparse import Namespace

import torch, json, ollama

from utils import load_model, generate, MODELS, TEMPLATES, PROMPTS
from nlu import NLU
from dm import DM
from nlg import NLG
from state_tracker import StateTracker
from conversation import Conversation


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

    conversation = Conversation(history_size=4)
    state_tracker = StateTracker()

    while True:
        user_input = input("User: ")
        conversation.update("user", user_input)

        # get the NLU output
        nlu_component = NLU(model, tokenizer, args)
        nlu_output = nlu_component(user_input, conversation.get_history(until=-1))
        print(f"NLU: {nlu_output}")
        if input("Continue? (y/n): ") == "n":
            break

        # update the state tracker
        state_tracker.update(nlu_output)
        print(f"State Tracker: {state_tracker.current_slots}")

        # get the DM output
        dm_component = DM(model, tokenizer, args, verbose=True)
        dm_output = dm_component(state_tracker)
        print(f"DM: {dm_output}")
        if input("Continue? (y/n): ") == "n":
            break

        # update the next best actions
        state_tracker.update_nba(dm_output)

        # get the NLG output
        nlg_component = NLG(model, tokenizer, args)
        nlg_output = nlg_component(dm_output, conversation.get_history())
        print(f"System: {nlg_output}")
        conversation.update("system", nlg_output)


if __name__ == "__main__":
    main()
