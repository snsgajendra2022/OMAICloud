"""
OM Automated Dataset Improvement Agent
"""


from .detector import DatasetProblemDetector

from .rewriter import SampleRewriter

from .history import ImprovementHistory





class DatasetImprovementAgent:



    def __init__(self):


        self.detector = DatasetProblemDetector()

        self.rewriter = SampleRewriter()

        self.history = ImprovementHistory()




    def improve(
        self,
        dataset:list[dict]
    ):



        improved=[]



        for item in dataset:


            problems = self.detector.detect(
                item
            )



            if problems:


                new_item = self.rewriter.rewrite(

                    item,

                    problems

                )


                self.history.save(
                    new_item
                )


                improved.append(
                    new_item
                )


            else:


                improved.append(
                    item
                )



        return {


            "input":

                len(dataset),


            "improved":

                len(improved),


            "dataset":

                improved

        }