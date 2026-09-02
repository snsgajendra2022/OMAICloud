from .base import BaseAgent



class GeneralAgent(BaseAgent):


    name="general"



    def can_handle(
        self,
        question
    ):

        return 0.3



    def execute(
        self,
        question,
        context=None
    ):


        return {


            "agent":

                self.name,


            "strategy":

                "general_conversation"


        }