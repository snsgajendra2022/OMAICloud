from .base_agent import BaseAgent

from .agent_model import AgentResult



class CriticAgent(BaseAgent):


    name="critic"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "critique":

                    "Review completed"

            },

            confidence=0.7

        )