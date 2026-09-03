"""
OM Knowledge Improvement Engine
"""


from .generator import TrainingExampleGenerator  # pyright: ignore[reportMissingImports]

from .dataset_writer import DatasetWriter





class KnowledgeImprovementEngine:



    def __init__(self):


        self.generator = TrainingExampleGenerator()

        self.writer = DatasetWriter()




    def improve(

        self,

        question,

        answer,

        evaluation

    ):


        if not evaluation.get(
            "approved",
            False
        ):

            return {


                "stored":
                    False,


                "reason":
                    "low quality answer"

            }



        example = self.generator.generate(

            question,

            answer,

            evaluation

        )


        self.writer.append(
            example
        )


        return {


            "stored":

                True,


            "dataset":

                str(

                    self.writer.path

                ),


            "category":

                example.category

        }