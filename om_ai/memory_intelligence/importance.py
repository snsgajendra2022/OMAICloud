"""
OM Memory Importance Scoring
"""



class ImportanceAnalyzer:



    def score(

        self,

        experience:dict

    ):


        score=0.0


        text=str(

            experience

        ).lower()



        important_words=[

            "architecture",

            "decision",

            "project",

            "solution",

            "error",

            "fix",

            "technology",

            "preference"

        ]



        for word in important_words:


            if word in text:

                score += 0.1



        return min(

            round(score,2),

            1.0

        )