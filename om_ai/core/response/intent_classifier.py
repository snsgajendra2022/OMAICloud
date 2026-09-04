class ResponseIntentClassifier:


    def classify(self, text):

        text = text.lower()


        if any(x in text for x in [
            "create",
            "build",
            "make",
            "develop",
            "code"
        ]):
            return "implementation"


        if any(x in text for x in [
            "why",
            "explain",
            "what is",
            "how"
        ]):
            return "explanation"


        if any(x in text for x in [
            "plan",
            "architecture",
            "design"
        ]):
            return "planning"


        return "general"