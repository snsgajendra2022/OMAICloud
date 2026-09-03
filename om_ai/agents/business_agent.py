"""
OM Business Agent

Handles:

- Business logic
- Finance
- Operations
"""


from .base import BaseAgent



class BusinessAgent(BaseAgent):


    name = "business"



    def can_handle(
        self,
        question: str
    ) -> float:


        keywords = [

            "business",
            "restaurant",
            "finance",
            "sales",
            "report",
            "management",
            "strategy"

        ]


        score = 0


        for word in keywords:

            if word in question.lower():

                score += 0.15


        return min(score,1.0)



    def execute(
        self,
        question,
        context=None
    ):


        return {


            "agent": self.name,


            "strategy":

                "business_analysis",


            "focus":

                [

                    "requirements",

                    "workflow",

                    "business rules",

                    "metrics"

                ]

        }