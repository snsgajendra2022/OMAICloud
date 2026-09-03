"""
OM Goal Progress Engine
"""





class GoalProgress:



    def calculate(

        self,

        milestones:list

    ):


        if not milestones:

            return 0



        completed=len(

            [

                m

                for m in milestones

                if m.get(
                    "status"
                )=="completed"

            ]

        )


        return round(

            completed /

            len(milestones),

            2

        )