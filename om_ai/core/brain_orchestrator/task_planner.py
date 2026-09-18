class TaskPlanner:


    def create_plan(
        self,
        context
    ):


        plan=[]


        if context.requires_research:

            plan.append(
                "research"
            )


        plan.append(
            "knowledge"
        )


        plan.append(
            "reasoning"
        )


        plan.append(
            "response"
        )


        return plan