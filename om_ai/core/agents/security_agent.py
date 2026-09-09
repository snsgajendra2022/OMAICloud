from .base_agent import BaseAgent


class SecurityAgent(BaseAgent):


    name="security"


    def execute(
        self,
        task,
        context=None
    ):


        return {

            "type":
                "security",

            "checked":
                True

        }