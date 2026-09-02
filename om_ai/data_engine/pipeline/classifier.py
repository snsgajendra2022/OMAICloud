"""
OM Data Engine
Knowledge Classification
"""

from __future__ import annotations



class KnowledgeClassifier:



    RULES = {


        "programming":[

            "python",
            "java",
            "react",
            "laravel",
            "fastapi",
            "database",
            "api",
            "code"

        ],


        "science":[

            "physics",
            "biology",
            "chemistry",
            "research"

        ],


        "business":[

            "finance",
            "accounting",
            "marketing"

        ]

    }



    def classify(
        self,
        text: str
    ) -> dict:


        lower = text.lower()


        domain = "general"

        technology = None



        for key, words in self.RULES.items():


            for word in words:


                if word in lower:


                    domain = key


                    if key == "programming":

                        technology = word


                    break



        return {

            "domain":
            domain,

            "technology":
            technology

        }