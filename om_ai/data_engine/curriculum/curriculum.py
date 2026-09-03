"""
OM Dataset Curriculum Builder

Creates learning progression.
"""


from .levels import DifficultyLevel





class DatasetCurriculum:



    def __init__(self):


        self.level = DifficultyLevel()




    def build(

        self,

        dataset:list[dict]

    ):


        curriculum = {


            "basic":[],

            "medium":[],

            "advanced":[]

        }



        for item in dataset:


            difficulty = item.get(

                "difficulty",

                "basic"

            )


            curriculum.setdefault(

                difficulty,

                []

            )


            curriculum[difficulty].append(

                item

            )



        return curriculum