class ImprovementPlanner:



    def plan(
        self,
        evaluation
    ):


        improvements=[]


        if evaluation["score"] < 0.5:

            improvements.append(
                "Improve response reasoning"
            )


        if evaluation["missing_context"]:

            improvements.append(
                "Improve memory retrieval"
            )


        return improvements