class PlanningEngine:



    def create_plan(
        self,
        steps
    ):


        return [

            {

                "step":index+1,

                "task":step

            }

            for index,step in enumerate(steps)

        ]