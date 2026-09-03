"""
OM Database Agent

Handles:

- Database design
- Schema planning
- Migration
- Data modeling
"""


from .base import BaseAgent



class DatabaseAgent(BaseAgent):


    name = "database"



    def can_handle(
        self,
        question: str
    ) -> float:


        keywords = [

            "database",
            "mysql",
            "sql",
            "schema",
            "migration",
            "table",
            "model",
            "query"

        ]


        score = 0


        for word in keywords:

            if word in question.lower():

                score += 0.15


        return min(score, 1.0)



    def execute(
        self,
        question,
        context=None
    ):


        return {


            "agent": self.name,


            "strategy":

                "database_engineering",


            "focus":

                [

                    "schema design",

                    "relationships",

                    "optimization",

                    "migration planning"

                ]

        }