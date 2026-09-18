class ConversationRouter:



    def detect(
        self,
        message:str
    ):


        text = message.lower().strip()



        if (
            "your name" in text
            or "who are you" in text
            or "what are you" in text
        ):

            return "identity"



        if (
            "good morning" in text
            or "goodmorning" in text
        ):

            return "morning"



        if (
            "good evening" in text
        ):

            return "evening"



        if text in [
            "hi",
            "hello",
            "hey"
        ]:

            return "greeting"

        if (
            text.startswith(("hi ", "hello ", "hey "))
            or "how are you" in text
            or "how r you" in text
            or "whats up" in text
            or "what's up" in text
        ):

            return "greeting"

        return None