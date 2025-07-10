import os
from utils.logger import get_logger
from components.state_tracker import StateTracker
from utils.utils import generate
from prompts.house_agency.nlg_prompts import NLG_PROMPTS

logger = get_logger(__name__)


class NLG:
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def select_nlg_prompt(self, next_best_action, conversation, state_tracker):
        if "show_houses" in next_best_action:
            logger.debug("Selecting show_houses prompt")
            return NLG_PROMPTS["show_houses"]
        elif "provide_info" in next_best_action:
            logger.debug("Selecting provide_info prompt")
            house_info = "House Info:\n" + str(state_tracker.active_house)
            return NLG_PROMPTS["provide_info"].format(conversation, house_info)
        elif "confirmation(COMPARE_HOUSES)" in next_best_action:
            logger.debug("Selecting compare_houses prompt")
            return NLG_PROMPTS["compare_houses"].format(
                conversation,
                state_tracker.houses_to_compare,
                state_tracker.properties_to_compare,
            )
        elif "confirmation" in next_best_action:
            logger.debug("Selecting confirmation prompt")
            return NLG_PROMPTS["provide_info"].format(conversation, "")
        elif "fallback_policy" in next_best_action:
            logger.debug("Selecting fallback_policy prompt")
            return NLG_PROMPTS["fallback_policy"].format(conversation, next_best_action)
        else:
            logger.debug("Selecting request_info prompt")
            return NLG_PROMPTS["request_info"].format(conversation)

    def __call__(self, state_tracker: StateTracker, conversation=[], stream=False):

        dm_output = [state_tracker.next_best_actions[-1]]
        state_tracker_state = state_tracker.get_state()

        nlg_outputs = []

        for next_best_action in dm_output:
            system_prompt = self.select_nlg_prompt(
                next_best_action, conversation, state_tracker
            )
            nlg_input = next_best_action + "\n" + str(state_tracker_state)
            system_prompt = self.args.chat_template.format(system_prompt, nlg_input)
            logger.debug(f"NLG Text: '{system_prompt}'")

            nlg_output = generate(self.model, system_prompt, self.tokenizer, self.args)
            nlg_outputs.append(nlg_output)

            self.post_process(nlg_outputs)

            return nlg_outputs[0]

    def post_process(self, nlg_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i in range(len(nlg_outputs)):
            nlg_outputs[i] = nlg_outputs[i].strip("\n")
            if len(nlg_outputs[i]) == 0:
                to_remove.append(i)

        for i in to_remove:
            nlg_outputs.pop(i)

        return nlg_outputs
