from .base_agent import BaseAgent

from .agent_model import AgentResult



class TrainerAgent(BaseAgent):


    name="trainer"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "training":

                    "dataset_ready"

            },

            confidence=0.8

        )