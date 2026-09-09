class AnswerPlanner:


    def plan(
        self,
        intent: str,
        message: str
    ):

        if intent == "coding":

            return [
                "Understand requirement",
                "Create technical plan",
                "Generate implementation",
                "Explain files",
                "Provide testing"
            ]


        if intent == "question":

            return [
                "Understand question",
                "Analyze information",
                "Create accurate answer"
            ]


        return [
            "Understand user goal",
            "Generate helpful response"
        ]