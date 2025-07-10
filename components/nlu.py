import os, json
from utils.logger import get_logger
from utils.utils import generate
from prompts.house_agency.nlu_prompts import NLU_PROMPTS

logger = get_logger(__name__)


class NLU:
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args

    def generate_chunks(self, user_input):
        prompt = NLU_PROMPTS[self.args.domain]["NLU"]["CHUNKING"]
        nlu_text = self.args.chat_template.format(prompt, user_input)
        nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
        nlu_output = nlu_output.strip()

        try:
            chunks = json.loads(nlu_output)
        except Exception as e:
            logger.error(
                "The NLU output [CHUNKING] is not in the expected json format. Output: '%s'",
                nlu_output,
            )
            raise e

        return chunks

    def classify_intent(self, user_input, conversation):
        path = os.path.join("prompts", self.args.domain, "intent.txt")
        system_prompt = open(path, "r").read()

        input_query = f"History:\n{conversation}\n\nUser: {user_input}"
        nlu_text = self.args.chat_template.format(system_prompt, input_query)
        nlu_output = generate(self.model, nlu_text, self.tokenizer, self.args)
        nlu_output = nlu_output.strip().strip("\n").strip("`")

        if (
            nlu_output.upper() not in NLU_PROMPTS.keys()
            and nlu_output.upper() != "OUT_OF_DOMAIN"
        ):
            logger.error(
                "The NLU output for intent classification is not in the expected format. Output: %s",
                nlu_output,
            )
        else:
            logger.debug("Intent identified: %s", nlu_output.upper())

        return [{"intent": nlu_output, "chunk": user_input}]

    def __call__(self, user_input, conversation=[], chunks=False):

        if chunks:
            chunks = self.generate_chunks(user_input)
            logger.debug("NLU Chunks found: %s", chunks)
        else:
            chunks = self.classify_intent(user_input, conversation)

        nlu_outputs = []

        for chunk in chunks:
            intent = chunk["intent"].upper()
            user_input = chunk["chunk"]
            if intent not in NLU_PROMPTS.keys():
                nlu_outputs.append(("OUT_OF_DOMAIN", {}))
                continue
            system_prompt = NLU_PROMPTS[intent].format(conversation)
            system_prompt = self.args.chat_template.format(system_prompt, user_input)
            nlu_output = generate(self.model, system_prompt, self.tokenizer, self.args)
            nlu_outputs.append((intent, nlu_output))

        self.post_process(nlu_outputs)

        return nlu_outputs

    def post_process(self, nlu_outputs):
        """
        Apply simple post-processing to the NLU outputs by converting them to a dictionary.
        """
        to_remove = []
        for i, (intent, nlu_output) in enumerate(nlu_outputs):
            if nlu_output == {}:  # OUT_OF_DOMAIN case
                nlu_outputs[i] = {"intent": intent, "slots": {}}
                continue

            try:
                if "{" in nlu_output and "}" in nlu_output:
                    nlu_output = nlu_output[
                        nlu_output.index("{") : nlu_output.index("}") + 1
                    ]
                nlu_output_dict = json.loads(nlu_output)
                nlu_outputs[i] = {"intent": intent, "slots": nlu_output_dict}
            except Exception as e:
                logger.error(
                    "The NLU output '%s' is not in the expected json format.",
                    nlu_output,
                )
                to_remove.append(i)

        for i in to_remove:
            nlu_outputs.pop(i)

        return nlu_outputs
