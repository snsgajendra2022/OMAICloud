"""
OM Training Domain Classifier
"""


class DomainClassifier:



    def classify(
        self,
        text:str
    ) -> str:


        value=text.lower()



        if any(

            x in value

            for x in [

                "python",

                "javascript",

                "api",

                "software",

                "code",

                "framework"

            ]

        ):

            return "engineering"



        if any(

            x in value

            for x in [

                "database",

                "sql",

                "mysql",

                "schema"

            ]

        ):

            return "database"



        if any(

            x in value

            for x in [

                "finance",

                "tax",

                "accounting",

                "business"

            ]

        ):

            return "business"



        if any(

            x in value

            for x in [

                "research",

                "paper",

                "science"

            ]

        ):

            return "research"



        return "general"