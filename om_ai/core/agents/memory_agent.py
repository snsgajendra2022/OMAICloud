from .base_agent import BaseAgent


class MemoryAgent(BaseAgent):


    name="memory"


    def execute(
        self,
        task,
        context=None
    ):


        return {

            "type":
                "memory",

            "operation":
                "retrieve_context"

        }