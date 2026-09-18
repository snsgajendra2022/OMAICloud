class DecisionEngine:



    def decide(
        self,
        context
    ):


        text=context.user_input.lower()



        if any(
            x in text
            for x in [
                "latest",
                "current",
                "compare",
                "research"
            ]
        ):

            context.requires_research=True



        return context