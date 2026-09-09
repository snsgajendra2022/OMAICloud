from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):


    name="research"


    def execute(
        self,
        task,
        context=None
    ):


        return {

            "type":
                "research",

            "task":
                task,

            "analysis":
                "Knowledge investigation required"

        }