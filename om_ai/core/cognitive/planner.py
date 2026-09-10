class PlanningEngine:


    def create_plan(
        self,
        goal
    ):


        return [

            {
            "step":1,
            "task":"Understand requirement"
            },

            {
            "step":2,
            "task":"Design solution"
            },

            {
            "step":3,
            "task":"Execute"
            },

            {
            "step":4,
            "task":"Verify"
            }

        ]


# Back-compat alias for package __init__ / docs
Planner = PlanningEngine
