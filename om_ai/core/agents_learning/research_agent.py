from .base_agent import BaseAgent

from .agent_model import AgentResult



class ResearchAgent(BaseAgent):


    name = "research"



    def execute(
        self,
        task
    ):


        return AgentResult(

            agent=self.name,

            success=True,

            output={

                "research_topic":
                    task.get(
                        "topic"
                    ),

                "status":
                    "research_ready"

            },

            confidence=0.7

        )