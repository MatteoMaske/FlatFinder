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
        tmp_chat = self.chat_history.copy()

        max_length = min(self.history_size, len(self.chat_history))
        tmp_chat = tmp_chat[-self.history_size:] if -self.history_size >= -max_length else tmp_chat[:max_length]

        for message in tmp_chat:
            formatted_chat += f"{message['role']}: {message['text']}\n"

        return formatted_chat
    
    def get_message(self,  idx: int):
        """
        Get the message at a specific index."
        """

        if abs(idx) > len(self.chat_history):
            return None
        else:
            return self.chat_history[idx]["text"]
    
    def reset(self, _for=None):
        self.chat_history = [{"role": "system", "text": "Hello! I am a conversational agent specialized on student's accomodation searching in India. How can I help you today?"}]

        if _for == "HOUSE_SELECTION":
            self.chat_history.append({"role": "system", "text": "I'd like a 2 BHK house in Mumbay under 10000 INR as rent, unfurnished please. I'd like it in the neighborhood of Bandra and at least 100 square feet."})
            self.chat_history.append({"role": "user", "text": "please show me the houses you found"})
            self.chat_history.append({"role": "system", "text": "Found 3 matching houses:\n\n1. Deep Heights, Nalasopara: 2 BHK , 790 sqft, ₹6.5k/month\n2. New Panvel: 2 BHK, 890 sqft, ₹8k/month\n3. Nakoda Heights, Nalasopara: 2 BHK, 550 sqft, ₹8k/month\n\nWhich one would you like to know more about?"})
        elif _for == "ASK_INFO":
            self.chat_history.append({"role": "system", "text": "Found 3 matching houses:\n\n1. Deep Heights, Nalasopara: 2 BHK , 790 sqft, ₹6.5k/month\n2. New Panvel: 2 BHK, 890 sqft, ₹8k/month\n3. Nakoda Heights, Nalasopara: 2 BHK, 550 sqft, ₹8k/month\n\nWhich one would you like to know more about?"})
            self.chat_history.append({"role": "user", "text": "I want to know more about the first house"})
            self.chat_history.append({"role": "system", "text": "Sure, what would you like to know about the first house?"})