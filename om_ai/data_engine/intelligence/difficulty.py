"""
OM Training Difficulty Detector
"""


class DifficultyDetector:



    def detect(

        self,

        text:str

    ) -> str:



        length=len(text.split())


        advanced_words=[

            "architecture",

            "distributed",

            "optimization",

            "scaling",

            "machine learning",

            "production"

        ]



        advanced=sum(

            1

            for word in advanced_words

            if word in text.lower()

        )



        if length > 80 or advanced >= 2:

            return "advanced"



        if length > 30 or advanced == 1:

            return "medium"



        return "basic"