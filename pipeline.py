import argparse
from argparse import Namespace

import torch, ollama, os

from utils.utils import load_model, MODELS, TEMPLATES
from components.nlu import NLU
from components.dm import DM
from components.nlg import NLG
from components.state_tracker import StateTracker
from utils.conversation import Conversation
from data.database import Database


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
        choices=os.listdir("prompts"),
        default="house_agency",
        help="The domain to use for the model."
    )
    parser.add_argument(
        "--database-path",
        type=str,
        default="house_dataset/House_Rent_Dataset.csv",
        help="The path to the csv file to use as database."
    )

    parsed_args = parser.parse_args()
    parsed_args.chat_template = TEMPLATES[parsed_args.model_name]
    parsed_args.model_name = MODELS[parsed_args.model_name]
    assert os.path.exists(parsed_args.database_path), "The database path does not exist."

    return parsed_args


def main():
    args = get_args()
    if args.model_name != "llama3:latest":
        model, tokenizer = load_model(args)
    else:
        ollama.show(args.model_name)
        model, tokenizer = None, None

    conversation = Conversation(history_size=4)
    database = Database(args.database_path)
    state_tracker = StateTracker(database)
    welcome_message = "Hello! I am a conversational agent specialized on student's accomodation searching in India. How can I help you today?"
    print(f"System: {welcome_message}")
    conversation.update("system", welcome_message)

    while True:
        user_input = input("User: ")
        conversation.update("user", user_input)

        # get the NLU output
        nlu_component = NLU(model, tokenizer, args)
        nlu_output = nlu_component(user_input, conversation.get_history(until=-1))
        print("="*50 + " NLU " + "="*50)
        print(f"NLU: {nlu_output}")

        # update the state tracker
        state_tracker.update(nlu_output)
        print(f"State Tracker: {state_tracker}")

        # get the DM output
        dm_component = DM(model, tokenizer, args)
        dm_output = dm_component(state_tracker)
        print("="*50 + " DM " + "="*50)
        print(f"DM: {dm_output}")

        # update the next best actions
        state_tracker.update_nba(dm_output)


        # get the NLG output
        nlg_component = NLG(model, tokenizer, args)
        nlg_output = nlg_component(state_tracker, conversation.get_history())
        print("="*50 + " NLG " + "="*50)
        print(f"System: {nlg_output}")
        conversation.update("system", nlg_output)


if __name__ == "__main__":
    main()
