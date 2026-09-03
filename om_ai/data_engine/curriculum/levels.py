"""
OM Training Difficulty Levels
"""


class DifficultyLevel:



    ORDER = {


        "basic": 1,


        "medium": 2,


        "advanced": 3


    }



    def score(
        self,
        level:str
    ) -> int:


        return self.ORDER.get(

            level,

            1

        )