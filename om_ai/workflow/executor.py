"""
OM Workflow Execution Engine

Responsible for:

- Dynamic agent allocation
- Agent execution
- QA validation
- Failure recovery
- Workflow learning
"""


from typing import Any


from om_ai.agents.allocation import AgentAllocator

from om_ai.workflow_memory import WorkflowLearningEngine

from om_ai.recovery import SelfHealingEngine

from om_ai.testing import TestingAgent





class WorkflowExecutor:


    def __init__(self):


        self.allocator = AgentAllocator()

        self.learning = WorkflowLearningEngine()

        self.recovery = SelfHealingEngine()

        self.testing = TestingAgent()



    def execute(

        self,

        workflow

    ) -> list[dict[str, Any]]:


        results = []

        workflow_success = True



        for task in workflow.tasks:


            allocation = self.allocator.allocate(

                task["title"]

            )


            execution_result = self._execute_agent(

                allocation,

                task

            )



            task_result = {


                "task":

                    task["title"],


                "agent":

                    allocation["selected_agent"],


                "confidence":

                    allocation["confidence"],


                "execution":

                    execution_result

            }



            # -----------------------------
            # Quality Testing
            # -----------------------------

            if allocation["selected_agent"] == "coding":


                qa_result = self.testing.evaluate(

                    task["title"],

                    str(execution_result)

                )


                task_result["quality"] = qa_result



            # -----------------------------
            # Failure Recovery
            # -----------------------------

            if execution_result.get(

                "status"

            ) == "failed":


                workflow_success = False


                recovery_result = self.recovery.recover(

                    task["title"],

                    execution_result.get(

                        "error",

                        "unknown error"

                    ),

                    allocation["selected_agent"]

                )


                task_result["recovery"] = recovery_result



            else:


                task_result["recovery"] = None



            results.append(

                task_result

            )



        # -----------------------------
        # Workflow Experience Learning
        # -----------------------------

        self.learning.learn(

            {

                "goal":

                    workflow.goal,


                "tasks":

                    workflow.tasks

            },

            success=workflow_success,

            score=1.0 if workflow_success else 0.5

        )


        return results




    def _execute_agent(

        self,

        allocation,

        task

    ):


        """

        Placeholder execution layer.

        Later connects with:

        AgentExecutor

        """



        try:


            return {


                "status":

                    "completed",


                "agent":

                    allocation["selected_agent"],


                "task":

                    task["title"],


                "output":

                    "Task execution completed"

            }



        except Exception as error:


            return {


                "status":

                    "failed",


                "error":

                    str(error)

            }