import argparse
from argparse import Namespace
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

import torch
import ollama

from utils.utils import load_model, MODELS, TEMPLATES
from components.nlu import NLU
from components.dm import DM
from components.nlg import NLG
from components.state_tracker import StateTracker
from utils.conversation import Conversation
from data.database import Database
from evaluator import Evaluator


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
        default=1500,
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

    # In case of evaluation
    parser.add_argument("--eval",action="store_true",help="whether launch the program in eval mode")
    parser.add_argument("--nlu_test_path", type=str, default="test/house_agency/nlu.json")
    parser.add_argument("--dm_test_path", type=str, default="test/house_agency/dm.json")

    parsed_args = parser.parse_args()

    if parsed_args.eval:
        assert parsed_args.nlu_test_path or parsed_args.dm_test_path, "Please provide the test paths for evaluation."

    parsed_args.chat_template = TEMPLATES[parsed_args.model_name]
    parsed_args.model_name = MODELS[parsed_args.model_name]
    assert os.path.exists(parsed_args.database_path), "The database path does not exist."

    return parsed_args


def start_chat(args):
    if args.model_name != "llama3:8b-instruct-q3_K_L":
        model, tokenizer = load_model(args)
    else:
        ollama.show(args.model_name)
        model, tokenizer = None, None

    conversation = Conversation(history_size=2)
    database = Database(args.database_path)
    state_tracker = StateTracker(database)
    print(f"System: {conversation.get_message(-1)}")
    # user_input = "please show me the houses you found"
    # conversation.update("user", user_input)
    # state_tracker.current_intent = "HOUSE_SEARCH"
    # state_tracker.current_slots = {"house_size": "100", "house_bhk": "2", "house_rent": "10000", "house_location": "Bandra", "house_city": "Mumbai", "house_furnished": "unfurnished"}
    # state_tracker.next_best_actions = ["confirmation(HOUSE_SEARCH)"]
    # state_tracker.handle_intent("HOUSE_SEARCH")
    # system_input = "Found 3 matching houses:\n\n1. Deep Heights, Nalasopara: 2 BHK , 790 sqft, ₹6.5k/month\n2. New Panvel: 2 BHK, 890 sqft, ₹8k/month\n3. Nakoda Heights, Nalasopara: 2 BHK, 550 sqft, ₹8k/month\n\nWhich one would you like to know more about?"
    # conversation.update("system", system_input)
    # user_input = "i want to know more about the first house"
    # conversation.update("user", user_input)
    # system_input = "Do you confirm that you want to know more about the first house?"
    # conversation.update("system", system_input)

    DEBUG = True
    
    while True:
        user_input = input("User: ")
        if user_input == "reset":
            conversation.reset()
            state_tracker.reset()
            print("System: Conversation reset.")
            continue

        # get the NLU output
        print("="*50 + " NLU " + "="*50) if DEBUG else None
        nlu_component = NLU(model, tokenizer, args)
        nlu_output = nlu_component(user_input, conversation.get_history())
        print(f"NLU: {nlu_output}") if DEBUG else None

        # update the conversation
        conversation.update("user", user_input)

        # update the state tracker
        state_tracker.update(nlu_output)
        print(f"State Tracker: {state_tracker.get_state()}") if DEBUG else None

        # get the DM output
        print("="*50 + " DM " + "="*50) if DEBUG else None
        dm_component = DM(model, tokenizer, args)
        dm_output = dm_component(state_tracker)
        print(f"DM: {dm_output}") if DEBUG else None

        # update the next best actions
        state_tracker.update_nba(dm_output)

        # get the NLG output
        print("="*50 + " NLG " + "="*50) if DEBUG else None
        nlg_component = NLG(model, tokenizer, args)
        nlg_output = nlg_component(state_tracker, conversation.get_history())
        print(f"System: {nlg_output}")
        conversation.update("system", nlg_output)

def evaluate(args):    
    if args.model_name != "llama3:8b-instruct-q3_K_L":
        model, tokenizer = load_model(args)
    else:
        ollama.show(args.model_name)
        model, tokenizer = None, None

    if args.nlu_test_path:
        assert os.path.exists(args.nlu_test_path), "The NLU test path does not exist."
    if args.dm_test_path:
        assert os.path.exists(args.dm_test_path), "The DM test path does not exist."

    # Initialize the conversation
    conversation = Conversation(history_size=2)
    # database = Database(args.database_path)
    # state_tracker = StateTracker(database)

    evaluator = Evaluator(args.nlu_test_path, args.dm_test_path)
    nlu_component = NLU(model, tokenizer, args)
    results = evaluator.evaluate_NLU(nlu_component, conversation)
    print(results)

if __name__ == "__main__":
    args = get_args()
    if args.eval:
        evaluate(args)
    else:
        start_chat(args)
