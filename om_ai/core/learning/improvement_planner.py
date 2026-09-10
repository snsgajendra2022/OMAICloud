class ImprovementPlanner:


    def create_plan(
        self,
        feedback
    ):


        plan=[]


        for issue in feedback["issues"]:

            if issue=="empty_response":

                plan.append(
                    "Improve generation stability"
                )


            if issue=="too_short":

                plan.append(
                    "Increase response depth"
                )


        return plan