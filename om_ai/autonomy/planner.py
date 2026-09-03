"""
OM Autonomous Planner

Breaks goals into executable tasks.
"""


from .goal import Goal




class AutonomousPlanner:



    def create_plan(
        self,
        goal:str
    ) -> Goal:



        tasks=[]



        text=goal.lower()



        if any(
            x in text
            for x in [
                "build",
                "create",
                "develop",
                "application",
                "system"
            ]
        ):


            tasks=[

                "Understand requirements",

                "Design architecture",

                "Create implementation plan",

                "Execute development",

                "Validate result"

            ]


        else:


            tasks=[

                "Analyze request",

                "Prepare solution"

            ]



        return Goal(

            description=goal,

            tasks=tasks,

            category="development"

        )