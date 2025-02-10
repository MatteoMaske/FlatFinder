class Conversation:
    def __init__(self, history_size=3):
        self.history_size = history_size
        self.chat_history = []

    def update(self, role: str, text):
        """
        Update the chat history with the new message.

        Args:
            role (str): The role of the speaker. Either 'user' or 'system'.
            text (str): The text of the message.
        """
        assert role in ["user", "system"], "Role must be either 'user' or 'system'."
        self.chat_history.append({"role": role, "text": text})
    
    def get_history(self, until=None):
        formatted_chat = ""

        max_length = min(self.history_size, len(self.chat_history))
        if until is not None:
            begin = -self.history_size+until if -self.history_size+until >= -max_length else -max_length
            end = until
        else:
            begin = -self.history_size if -self.history_size >= -max_length else -max_length
            end = len(self.chat_history)

        for i in range(begin, end):
            formatted_chat += f"{self.chat_history[i]['role']}: {self.chat_history[i]['text']}\n"

        return formatted_chat