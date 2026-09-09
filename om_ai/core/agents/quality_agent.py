from .base_agent import BaseAgent


class QualityAgent(BaseAgent):


    name="quality"


    def execute(
        self,
        task,
        context=None
    ):


        return {

            "type":
                "quality",

            "validation":
                "required"

        }