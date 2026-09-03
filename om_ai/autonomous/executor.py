"""
OM Autonomous Task Executor
"""


from om_ai.collaboration import AgentCoordinator

class TaskExecutor:



    def __init__(

        self,

        agent_executor=None

    ):


        self.agent_executor=agent_executor
        self.coordinator = AgentCoordinator()




    def execute(

        self,

        task,

        context=None

    ):


        context=context or {}

        self.coordinator.collaborate(

            task.to_dict(),

            [

                task.agent

            ]

        )

        if self.agent_executor:


            result=self.agent_executor.execute(

                {

                    "name":
                        task.agent,

                    "agent":
                        task.agent

                },

                task.description,

                context

            )


        else:


            result={

                "message":

                "No execution engine connected"

            }



        task.complete(

            result

        )


        return task