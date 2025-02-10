from argparse import Namespace
from typing import Tuple

import torch, ollama
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BatchEncoding,
    PreTrainedTokenizer,
    PreTrainedModel
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

    # HOUSE_AGENCY template =================================
    "HOUSE_AGENCY": {} # To validate args.domain
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
    print(f"Inputs number of tokens: {len(inputs.input_ids[0])}")
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
        return response["response"]
    else:
        input_tokens = tokenizer(text, return_tensors="pt").to(model.device)
        return model_generate(model, input_tokens, tokenizer, args)