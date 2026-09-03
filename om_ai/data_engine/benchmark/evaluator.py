"""
OM Dataset Evaluator
"""


from .metrics import DatasetMetrics





class DatasetEvaluator:



    def __init__(self):

        self.metrics = DatasetMetrics()




    def evaluate(
        self,
        item:dict
    ) -> dict:


        completeness = self.metrics.completeness(
            item
        )


        length = self.metrics.length_quality(
            item
        )


        diversity = self.metrics.diversity(
            item
        )


        score = (

            completeness *0.5

            +

            length *0.3

            +

            diversity *0.2

        )


        return {


            "score":

                round(score,3),


            "approved":

                score >=0.7,


            "metrics":

            {

                "completeness":

                    completeness,


                "length":

                    length,


                "diversity":

                    diversity

            }

        }