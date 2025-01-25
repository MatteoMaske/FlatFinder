from argparse import Namespace
from typing import Tuple

import torch, ollama
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BatchEncoding,
    PreTrainedTokenizer,
    PreTrainedModel,
)

MODELS = {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "llama3": "meta-llama/Meta-Llama-3-8B-Instruct",
    "ollama": "llama3:latest",
}

TEMPLATES = {
    "llama2": "<s>[INST] <<SYS>>\n{}\n<</SYS>>\n\n{} [/INST]",
    "llama3": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
    "ollama": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
}

PROMPTS = {
    # PIZZA template =================================
    "PIZZA": {
    "NLU": """Identify the user intent from this list:
[pizza_ordering, pizza_delivery, drink_ordering, out_of_domain].
If the intent is pizza_ordering, extract the following slot values from the user input
- pizza_size, the size of the pizza
- pizza_type, the type of pizza
- pizza_count, the number of pizzas.
If no values are present in the user input you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "intent": "intent_value",
    "slots": {
        "slot1": "value1",
        "slot2": "value2",
        "slot3": "value3"
    }
}""",

    "DM": """You are the Dialogue Manager.
Given the output of the NLU component, you should only generate the next best action from this list:
- request_info(slot), if a slot value is missing (null) by substituting slot with the missing slot name
- confirmation(intent), if all slots have been filled""",

    "NLG": """You are the NLG component: you must be very polite.
Given the next best action classified by the Dialogue Manager (DM),
you should only generate a lexicalized response for the user.
Possible next best actions are:
- request_info(slot): generate an appropriate question to ask the user for the missing slot value
- confirmation(intent): generate an appropriate confirmation message for the user intent"""
    },

    # AMATRICIANA template =================================
    "AMATRICIANA": {
        "NLU": {
            "CHUNKING": """You are an intelligent NLU component of a conversational agent that analyzes user request for different intents. Here is a list of intents:
- pasta_ordering
- pasta_delivery
- drink_ordering
- request_information
- out_of_domain

Task:
1. Divide the input text into sentences or chunks.
2. Assign each chunk to one of the intents from the list. If no intent matches, label it as "out_of_domain".
3. Respond in the following JSON format:
[
    {"chunk": "chunk 1 text", "intent": "identified intent"},
    {"chunk": "chunk 2 text", "intent": "identified intent"},
    ...
]

Only output a valid JSON object.
""",
            "PASTA_ORDERING": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request. 
Extract the following slot values from a chunk of the user input for the intent "pasta_ordering":
- sauce, "with onions" or "without onions"
- cream, "very creamy" or "low creamy"
- size, "reduced" or "normal"
- meet, "pancetta" or "guanciale"
- parmesan, "on top" or "in the sauce"
- pasta_type, "penne" or "spaghetti" or "maccheroni"

If no values are present in the user input you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}""",
            "PASTA_DELIVERY": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "pasta_delivery":
- address, the delivery address
- phone, the phone number
- order_time, the time of delivery

If no values are present in the user input you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}""",
            "DRINK_ORDERING": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "drink_ordering":
- drink_type, the type of drink
- drink_size, the size of the drink
- drink_count, the number of drinks

If no values are present in the user input you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}""",   
        },

    "DM": """You are the Dialogue Manager.
Given the output of the NLU component, you should only generate the next best action from this list:
- request_info(slot), if a slot value is missing (null) by substituting slot with the missing slot name
- confirmation(intent), if all slots have been filled""",

    "NLG": """You are the NLG component: you must be very polite.
Given the next best action classified by the Dialogue Manager (DM),
you should only generate a lexicalized response for the user.
Possible next best actions are:
- request_info(slot): generate an appropriate question to ask the user for the missing slot value
- confirmation(intent): generate an appropriate confirmation message for the user intent"""
    },  

    # HOUSE AGENCY template =================================
    "HOUSE_AGENCY": {
        "NLU": {
            "CHUNKING": """You are an intelligent NLU component of a conversational agent that analyzes user requests for different intents. Here is a list of intents:
- house_search, request for a house specifying different attributes to guide the search
- ask_info, request for specific information about a specific house (contract, housemates, location etc.)
- compare_houses, comparison between two houses or apartments
- out_of_domain

Task:
1. Analyze the input text and divide it into sentences or phrases representing user requests for a specific intent.
2. Assign each text to one of the intents from the list. If no intent matches, label it as "out_of_domain".
3. Respond in the following JSON format:
[
    {"chunk": "text 1", "intent": "identified intent"},
    {"chunk": "text 2", "intent": "identified intent"},
    ...
]

Only output a valid JSON object without any additional information.
""",
            "INTENT": """You are an intelligent NLU component of a conversational agent that analyzes user requests for different intents. Here is a list of intents:
- house_search, request for a house specifying different attributes to guide the search
- ask_info, request for specific information about a specific house (contract, housemates, location etc.)
- compare_houses, comparison between two houses or apartments
- out_of_domain

Task:
1. Given an optional history of the conversation and a new user input, classify the intent of the user request.
2. Respond with the name of the identified intent.

History:
{}

Only output the intent name.
""",
            "HOUSE_SEARCH": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "house_search":
- house_type, the type of house
- house_size, the size of the house
- house_price, the price of the house
- house_location, the location of the house

If no values are present in the user input you have to put null as the value.
Output them in a json format.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}

Output only a valid JSON object without any additional information.
""",
            "HOUSE_INFO": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "house_info":
- house_reference, a unique identifier or description of the house the user is referring to
- specific_info, the specific information the user is requesting about the house (e.g., price, size, condition, location, amenities, or any other detail)
- context, any additional context provided by the user about their request (e.g., comparisons, preferences, or time-related questions)

If no values are present in the user input, you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}
""",
            "CONTRACT_INFO": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "contract_info":
- start_date, the starting date of the contract
- rent_amount, the monthly rent amount
- extra_costs, any additional costs associated with the contract (e.g., utilities, maintenance fees)
- deposit_amount, the amount required as a deposit
- min_duration, the minimum length for which the contract has to be signed (e.g., 6 months, 1 year)
- cancellation_policy, the policy regarding early termination or cancellation of the contract
- other_conditions, any other specific conditions or clauses mentioned in the contract

If no values are present in the user input, you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}
""",
            "LOCATION_INFO": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "location_info":
- house_address, the specific address or location of the house
- neighborhood, the name or description of the surrounding area
- nearby_amenities, amenities or facilities near the location (e.g., grocery stores, gyms, parks)
- transport_options, available public transportation options or proximity to major transit hubs (e.g., bus stops, metro stations)
- safety_level, any mention of the safety or security of the area
- distance_to_point, the distance to a specific point of interest (e.g., university, workplace, city center)
- other_location_details, any additional information about the location not captured by the other slots

If no values are present in the user input, you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}
""",
            "APARTMENT_LIFE": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "apartment_life":
- number_of_occupants, the total number of people currently living in the apartment
- occupant_types, the type or demographic of the occupants (e.g., students, professionals, families)
- shared_spaces, details about shared spaces in the apartment (e.g., kitchen, living room, bathroom)
- apartment_rules, any specific rules or policies mentioned (e.g., no smoking, quiet hours)
- compatibility_info, information about compatibility or preferences for living arrangements (e.g., looking for quiet people, non-smokers)
- other_apartment_details, any additional information about life in the apartment not captured by the other slots

If no values are present in the user input, you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}
""",
            "ASK_INFO": """You are an intelligent NLU component of a conversational agent that analyzes chunks of user request.
Extract the following slot values from a chunk of the user input for the intent "ask_info":
- house_reference, a unique identifier or description of the house the user is referring to
- specific_info, the specific information the user is requesting about the house (e.g., price, size, condition, location, amenities, or any other detail)
- context, any additional context provided by the user about their request (e.g., comparisons, preferences, or time-related questions)

If no values are present in the user input, you have to put null as the value.
Output them in a json format.
Only output the json file.
The json format is:
{
    "slot1": "value1",
    "slot2": "value2",
    "slot3": "value3",
    ...
}
""",
    },

    "DM": """You are an intelligent component of a conversational agent that acts as the Dialogue Manager.
Given the output of the NLU component, you should generate the next best action from this list:
- request_info(slot), if a slot value is missing (None) by substituting slot with the missing slot name
- confirmation(intent), if all slots have been filled with a not null value

Guidelines:
- Use only the given intent and slots to generate the next best action.

Please do not include other information other than the next best action.""",

    "NLG": """You are the NLG component: you must be very polite.
Given the next best action classified by the Dialogue Manager (DM), you should generate a lexicalized response for the user.
Possible next best actions are:
- request_info(slot): generate an appropriate question to ask the user for the missing slot value
- confirmation(intent): generate an appropriate confirmation message for the user intent

Please be coherent with the following chat history:
{}

Please do not include other information other than the response."""
    },  
}


def load_model(args: Namespace) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        device_map="auto" if args.parallel else args.device, 
        torch_dtype=torch.float32 if args.dtype == "f32" else torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    return model, tokenizer  # type: ignore


def model_generate(
    model: PreTrainedModel,
    inputs: BatchEncoding,
    tokenizer: PreTrainedTokenizer,
    args: Namespace,
) -> str:
    output = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=args.max_new_tokens,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(
        output[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
    )

def generate(model, text, tokenizer, args):
    if model is None:
        response = ollama.generate(args.model_name, text, raw=True)
        output = response["response"]
    else:
        nlu_input = tokenizer(text, return_tensors="pt").to(model.device)
        output = model_generate(model, nlu_input, tokenizer, args)

    return output