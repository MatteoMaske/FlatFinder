import sys
import traceback
from utils.logger import get_logger

from data.database import Database

logger = get_logger(__name__)


class StateTracker:
    """The state tracker class is responsible for keeping track of the state of the system.
    It keeps track of the current intent, slots, and the next best actions to be taken by the system.

    Attributes:
        database (Database): The database object
        current_intent (str): The current intent of the user request
        current_slots (dict): The current slots of the user request
        next_best_actions (list): The next best actions to be taken by the system
        current_houses (list): The current houses found in the database
        houses_to_compare (list): The houses to be compared
        properties_to_compare (list): The properties to be compared
        active_house (House): The active house selected by the user
    """

    def __init__(self, database: Database):
        self.database = database
        self.last_active_state = None

        # Tracked from NLU
        self.current_intent = None
        self.current_slots = {}

        # Tracked from DM
        self.next_best_actions = []

        # HOUSE_SEARCH information
        self.current_houses = []

        # ASK_INFO information
        self.active_house = None

        # COMPARE_HOUSES information
        self.houses_to_compare = []
        self.properties_to_compare = []

    def update(self, nlu_output):

        if not isinstance(nlu_output, list) or len(nlu_output) == 0:
            self.fallback_policy(
                "An error occured in processing the user request. Please try again."
            )
            return

        for chunk in nlu_output:
            intent, slots = chunk["intent"], chunk["slots"]

            if intent not in [
                "HOUSE_SEARCH",
                "HOUSE_SELECTION",
                "ASK_INFO",
                "COMPARE_HOUSES",
                "OUT_OF_DOMAIN",
            ]:
                self.fallback_policy(
                    "Unknown intent for the current system, please try again."
                )
            elif intent == "OUT_OF_DOMAIN":
                self.fallback_policy(
                    "The intent of the user request is out of the domain of the current system."
                )
            else:
                self.current_intent = intent
                self.initialize_slots(intent, slots)

            if not self.current_intent:  # Initial state
                self.current_intent = intent
                self.initialize_slots(intent, slots)
            elif intent == self.current_intent:  # Same intent
                changed = self.update_slots(slots)

                if self.check_slots(self.current_slots):
                    self.handle_intent(intent, changed)
            else:
                if not self.check_slots(self.current_slots):
                    self.fallback_policy(
                        "Unfortunatly, it seems that the task you are trying to perform is not coherent with the current state of the system. Please try again."
                    )
                else:
                    self.current_intent = intent
                    self.current_slots = slots
                    logger.debug("Changing intent to %s with slots %s", intent, slots)
                    self.initialize_slots(intent, slots)

    def initialize_slots(self, intent, slots):
        """Initialize the slots for the current intent.
        Make sure that all the slots for a given intent are inserted in the current_slots dictionary.
        """
        if intent == "HOUSE_SEARCH":
            self.current_slots = {
                "house_size": None,
                "house_bhk": None,
                "house_rent": None,
                "house_location": None,
                "house_city": None,
                "house_furnished": None,
            }
            for key, value in slots.items():
                if value is not None and value != "None" and value != "null":
                    self.current_slots[key] = value
        elif intent == "HOUSE_SELECTION":
            self.current_slots = {"house_selected": None}
            for key, value in slots.items():
                if value is not None and value != "None" and value != "null":
                    self.current_slots[key] = value
            self.handle_intent(intent, False)
        elif intent == "ASK_INFO":
            if not self.active_house:
                self.fallback_policy(
                    "No house selected, you must search or select a house first."
                )
            else:
                self.current_slots = slots
        elif intent == "COMPARE_HOUSES":
            if not self.current_houses:
                self.fallback_policy(
                    "No houses found to be compared, you must search for houses first."
                )
            else:
                try:
                    self.houses_to_compare = [
                        self.current_houses[idx] for idx in slots["houses"]
                    ]
                    self.properties_to_compare = slots["properties"]
                    logger.info("Comparing houses: %s", self.houses_to_compare)
                except Exception as e:
                    logger.error(
                        "Error in parsing the compare houses intent: %s",
                        traceback.format_exc(),
                    )
                    self.fallback_policy(
                        "Error in processing the user request. Please try again."
                    )
        else:
            raise Exception(
                f"❌Error: Initializing slots for an unknown intent {intent}."
            )

    def check_slots(self, slots: dict):
        """Check if all the slots are filled for the current intent"""
        for val in slots.values():
            if not val:
                return False
        return True

    def update_slots(self, slots):
        """Update the current slots with the new slots

        Args:
            slots (dict): The slots of the user request

        Returns:
            changed (bool): If the slots have been changed in the current turn
        """

        prev_slots = self.current_slots.copy()
        for key, value in slots.items():
            if value is not None and value != "None" and value != "null":
                self.current_slots[key] = value
        if (
            self.check_slots(self.current_slots)
            and self.check_slots(prev_slots)
            and self.current_intent == "HOUSE_SEARCH"
        ):
            logger.debug("Slots changed: %s -> %s", prev_slots, self.current_slots)
            return sorted(prev_slots.values()) != sorted(self.current_slots.values())
        else:
            return False

    def update_nba(self, dm_output: str):
        self.next_best_actions.append(dm_output)

    def handle_intent(self, intent, changed: bool):
        """Handles one intent, once its slots are filled

        Args:
            intent (str): The intent of the user request
            changed (bool): If the slots have been changed in the current turn
        """

        if intent == "HOUSE_SEARCH":
            if (
                "confirmation" in self.next_best_actions[-1]
                and "HOUSE_SEARCH" in self.next_best_actions[-1]
                and not changed
            ):
                self.current_houses = self.database.get_houses(self.current_slots)
                houses = self.current_houses
                self.current_intent = "SHOW_HOUSES"
                self.current_slots = {
                    f"option_{i}": str(house) for i, house in enumerate(houses)
                }
                logger.info("The search resulted in %d houses.", len(houses))
        elif intent == "HOUSE_SELECTION":
            if self.current_slots["house_selected"] is not None:
                try:
                    index = int(self.current_slots["house_selected"])
                    self.active_house = self.current_houses[index - 1]
                    logger.info("House activated: %s", self.active_house)
                    self.current_intent = "ASK_INFO"
                    self.current_slots = {"properties": None}
                except Exception:
                    logger.error("Error in parsing the house selection intent")
                    self.fallback_policy(
                        "Error in processing the user selection. Please reselect the house."
                    )
        elif intent == "COMPARE_HOUSES":
            self.properties_to_compare = self.current_slots["properties"]
            if self.houses_to_compare == []:
                try:
                    self.houses_to_compare = [
                        self.current_houses[i] for i in self.current_slots["houses"]
                    ]
                except Exception:
                    logger.error("Error in parsing the compare houses intent")
                    self.current_intent = "COMPARE_HOUSES"
                    self.current_slots = {"houses": None, "properties": None}
        elif intent == "ASK_INFO":
            if not self.active_house:
                self.fallback_policy(
                    "No house selected, you must search or select a house first."
                )
        else:
            raise Exception(f"StateTracker Error: Handling an unknown intent {intent}.")

    def get_state(self) -> dict:
        info = {"intent": self.current_intent, "slots": self.current_slots}
        return info

    def fallback_policy(self, reason: str):
        logger.warning("Fallback policy activated: %s", reason)
        logger.debug("Saving last active state: %s", self.get_state())

        self.last_active_state = self.get_state()
        self.current_intent = "FALLBACK_POLICY"
        self.current_slots = {"reason": reason}

    def reset(self):
        self.current_intent = None
        self.current_slots = {}
        self.next_best_actions = []
        self.current_houses = []
        self.houses_to_compare = []
        self.properties_to_compare = []
        self.active_house = None
