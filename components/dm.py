import os

from utils.utils import generate
from .state_tracker import StateTracker

class DM:
    """ Dialogue Manager (DM) class for managing dialogue states and generating responses.
    This class is responsible for interpreting the current state of the dialogue and generating appropriate outputs.
    """
    def __init__(self, model, tokenizer, args, verbose=False):  
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.verbose = verbose

    def __call__(self, current_state, deterministic=False) -> str:
        """ Generate the dialogue manager output based on the current state. 
        Args:
            current_state (dict): The current state of the dialogue.
            deterministic (bool): If True, the output will be deterministic.

        Returns:
            str: The generated dialogue manager output.
        """

        if current_state["intent"] == "SHOW_HOUSES" and current_state["slots"] != {}:
            return "show_houses(HOUSE_SEARCH)"
        elif current_state["intent"] == "SHOW_HOUSES" and current_state["slots"] == {}:
            return "fallback_policy('No houses found for the given search criteria.')"
        elif current_state["intent"] == "FALLBACK_POLICY":
            reason = current_state["slots"]["reason"]
            return f'fallback_policy("{reason}")'      
        
        if deterministic:
            return self.deterministic_choice(current_state)
        
        path = os.path.join("prompts", self.args.domain, "dm.txt")
        system_prompt = open(path, "r").read()
        system_prompt = self.args.chat_template.format(system_prompt, str(current_state))

        print(f"DM Text: '{system_prompt}'") if self.verbose else None
        dm_output = generate(self.model, system_prompt, self.tokenizer, self.args)

        return self.post_process(dm_output)
    
    def post_process(self, dm_output: str):
        """
        Apply simple post-processing to the DM outputs by converting them to a dictionary.
        """
        dm_output = dm_output.strip("\n")            

        return dm_output
    
    def deterministic_choice(self, current_state):
        """ 
        Generate a deterministic choice based on the current state.
        """
        missing_slots = [slot for slot, value in current_state["slots"].items() if value is None or value == "" or value == []]
        if len(missing_slots) > 0:
            return f'request_slot("{missing_slots[0]}")'
        elif current_state["intent"] != "ASK_INFO":
            return f'confirmation("{current_state["intent"]}")'
        else:
            if current_state["slots"]["properties"]:
                return f'provide_info("{current_state["slots"]["properties"][0]}")'
            else:
                return "fallback_policy('No properties information asked, please retry.')"