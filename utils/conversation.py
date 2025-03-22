class Conversation:
    def __init__(self, history_size=3):
        self.history_size = history_size
        self.reset()

    def update(self, role: str, text):
        """
        Update the chat history with the new message.

        Args:
            role (str): The role of the speaker. Either 'user' or 'system'.
            text (str): The text of the message.
        """
        assert role in ["user", "system"], "Role must be either 'user' or 'system'."
        self.chat_history.append({"role": role, "text": text})
    
    def get_history(self):
        formatted_chat = ""

        max_length = min(self.history_size, len(self.chat_history))
        begin = -self.history_size if -self.history_size >= -max_length else -max_length
        end = len(self.chat_history)

        for i in range(begin, end):
            formatted_chat += f"{self.chat_history[i]['role']}: {self.chat_history[i]['text']}\n"

        return formatted_chat
    
    def get_message(self,  idx: int):
        """
        Get the message at a specific index."
        """

        if abs(idx) > len(self.chat_history):
            return None
        else:
            return self.chat_history[idx].text
    
    def reset(self):
        self.chat_history = [{"role": "system", "text": "Hello! I am a conversational agent specialized on student's accomodation searching in India. How can I help you today?"}]