"""
OM Training Example Generator

Converts successful OM experiences
into SFT training examples.
"""


from .example import TrainingExample





class TrainingExampleGenerator:



    def generate(

        self,

        question: str,

        answer: str,

        evaluation: dict

    ) -> TrainingExample:



        return TrainingExample(

            instruction=question,

            response=answer,

            category=self.detect_category(
                question
            ),

            quality_score=float(

                evaluation.get(
                    "score",
                    0.0
                )

            ),

            metadata={

                "approved":

                    evaluation.get(
                        "approved",
                        False
                    )

            }

        )



    def detect_category(

        self,

        question: str

    ) -> str:



        q = question.lower()



        if any(

            word in q

            for word in [

                "code",

                "api",

                "software",

                "application",

                "build",

                "develop"

            ]

        ):

            return "engineering"



        if any(

            word in q

            for word in [

                "finance",

                "business",

                "report",

                "sales"

            ]

        ):

            return "business"



        if any(

            word in q

            for word in [

                "database",

                "sql",

                "mysql",

                "schema"

            ]

        ):

            return "database"



        return "general"