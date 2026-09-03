"""
OM Long Running Task Scheduler
"""





class GoalScheduler:



    def next_task(

        self,

        goal

    ):


        for milestone in goal.get(

            "milestones",

            []

        ):


            if milestone.get(

                "status"

            ) != "completed":


                return milestone



        return None