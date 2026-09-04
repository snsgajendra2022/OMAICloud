class ResponseIntentClassifier:


    def classify(self, text):

        text = text.lower()


        if any(
            word in text
            for word in [
                "create",
                "build",
                "make",
                "write code"
            ]
        ):

            return "implementation"


        if any(
            word in text
            for word in [
                "architecture",
                "design system",
                "best practice"
            ]
        ):

            return "architecture"


        if any(
            word in text
            for word in [
                "explain",
                "what is",
                "how"
            ]
        ):

            return "explanation"


        return "general"