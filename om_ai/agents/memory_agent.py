"""
OM Memory Agent

Handles:

- User memory
- Project memory
- Context recall
"""


from .base import BaseAgent




class MemoryAgent(BaseAgent):


    name = "memory"



    def can_handle(
        self,
        question:str
    ) -> float:


        return 0.5



    def execute(
        self,
        question,
        context=None
    ):


        return {


            "agent": self.name,


            "strategy":

                "memory_retrieval",


            "focus":

                [

                    "previous conversations",

                    "project context",

                    "long term knowledge"

                ]

        }