from .base_agent import BaseAgent

from .agent_model import AgentResult



class EvaluatorAgent(BaseAgent):


    name="evaluator"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "score":

                    0.8

            },

            confidence=0.8

        )