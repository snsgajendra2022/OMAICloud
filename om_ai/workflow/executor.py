"""
OM Workflow Execution Engine
"""


from om_ai.agents.allocation import AgentAllocator





class WorkflowExecutor:



    def __init__(self):


        self.allocator = AgentAllocator()




    def execute(

        self,

        workflow

    ):


        results=[]



        for task in workflow.tasks:


            allocation = self.allocator.allocate(

                task["title"]

            )



            results.append(

                {

                    "task":

                        task["title"],


                    "agent":

                        allocation["selected_agent"],


                    "confidence":

                        allocation["confidence"],


                    "status":

                        "ready"

                }

            )



        return results