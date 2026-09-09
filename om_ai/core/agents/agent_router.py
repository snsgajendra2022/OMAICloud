class AgentRouter:


    def select(
        self,
        understanding,
        reasoning
    ):


        agents=[]


        intent = (
            understanding
            .get(
                "intent",
                ""
            )
        )


        if intent == "coding":

            agents.append(
                "coding"
            )


        if intent == "research":

            agents.append(
                "research"
            )


        agents.append(
            "quality"
        )


        return agents