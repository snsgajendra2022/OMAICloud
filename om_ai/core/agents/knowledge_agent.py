from .base_agent import BaseAgent


class KnowledgeAgent(BaseAgent):


    name="knowledge"


    def execute(
        self,
        task,
        context=None
    ):


        return {

            "type":
                "knowledge",

            "operation":
                "retrieve_information"

        }