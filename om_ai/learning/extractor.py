"""
OM Experience Extractor

Converts execution result into memory.
"""


from .experience import Experience





class ExperienceExtractor:



    def extract(

        self,

        question: str,

        answer: str,

        evaluation: dict

    ) -> Experience:



        score = float(

            evaluation.get(
                "score",
                0
            )

        )



        return Experience(

            question=question,

            answer=answer,

            score=score,

            success=evaluation.get(
                "approved",
                False
            ),

            category=self.detect_category(
                question
            )

        )




    def detect_category(
        self,
        question:str
    ):


        q = question.lower()


        if any(
            x in q
            for x in [
                "code",
                "build",
                "api",
                "software"
            ]
        ):

            return "engineering"



        if any(
            x in q
            for x in [
                "business",
                "finance",
                "report"
            ]
        ):

            return "business"



        return "general"