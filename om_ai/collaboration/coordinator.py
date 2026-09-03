"""
OM Multi Agent Coordinator
"""


from .bus import CommunicationBus

from .workspace import AgentWorkspace

from .memory import AgentMemory





class AgentCoordinator:



    def __init__(self):


        self.bus = CommunicationBus()

        self.workspace = AgentWorkspace()

        self.memory = AgentMemory()




    def collaborate(

        self,

        task:dict,

        agents:list[str]

    ):


        messages=[]



        for agent in agents:


            messages.append(

                self.bus.send(

                    "orchestrator",

                    agent,

                    (

                        "Execute task: "

                        +

                        task.get(

                            "description",

                            ""

                        )

                    ),

                    "task_assignment"

                )

            )



        return {


            "task":

                task,


            "agents":

                agents,


            "messages":

                messages

        }