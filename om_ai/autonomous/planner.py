"""
OM Autonomous Task Planner
"""


from .task import Task




class AutonomousPlanner:



    def create_plan(

        self,

        goal:str

    ):


        tasks=[]



        if any(

            x in goal.lower()

            for x in [

                "app",

                "software",

                "system",

                "platform"

            ]

        ):


            tasks=[


                Task(

                    id="task_1",

                    title="Requirement Analysis",

                    description="Understand system requirements",

                    agent="research"

                ),


                Task(

                    id="task_2",

                    title="Architecture Design",

                    description="Create technical architecture",

                    agent="coding",

                    depends_on=[

                        "task_1"

                    ]

                ),


                Task(

                    id="task_3",

                    title="Implementation",

                    description="Build application modules",

                    agent="coding",

                    depends_on=[

                        "task_2"

                    ]

                ),


                Task(

                    id="task_4",

                    title="Testing",

                    description="Validate implementation",

                    agent="testing",

                    depends_on=[

                        "task_3"

                    ]

                )

            ]


        else:


            tasks=[


                Task(

                    id="task_1",

                    title="Analyze Request",

                    description=goal

                )

            ]



        return tasks