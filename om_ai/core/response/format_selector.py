class FormatSelector:


    def select(
        self,
        message,
        intent
    ):


        text = message.lower()


        if intent == "coding":

            return "technical"


        if "step" in text:

            return "step_by_step"


        if "explain" in text:

            return "explanation"


        return "conversation"