"""
OM Improvement Evaluation Engine
"""


class ImprovementEvaluator:



    def evaluate(

        self,

        old_score,

        new_score

    ):


        return {


            "improved":

                new_score > old_score,


            "difference":

                new_score - old_score

        }