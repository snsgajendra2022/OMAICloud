from .base_agent import BaseAgent

from .agent_model import AgentResult



class TeacherAgent(BaseAgent):


    name="teacher"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "training_example":

                    task

            },

            confidence=0.8

        )