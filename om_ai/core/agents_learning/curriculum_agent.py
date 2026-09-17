from .base_agent import BaseAgent

from .agent_model import AgentResult



class CurriculumAgent(BaseAgent):


    name="curriculum"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "learning_plan":

                [

                    task.get(
                        "topic"
                    )

                ]

            },

            confidence=0.8

        )