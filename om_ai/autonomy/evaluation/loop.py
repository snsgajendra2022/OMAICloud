"""
OM Self Correction Loop
"""


from .quality_checker import QualityChecker

from .correction import CorrectionPlanner





class SelfCorrectionLoop:



    def __init__(self):


        self.checker = QualityChecker()

        self.corrector = CorrectionPlanner()




    def review(

        self,

        result:str

    ):


        evaluation = self.checker.evaluate(

            result

        )



        if evaluation["approved"]:


            return {


                "approved":

                    True,


                "evaluation":

                    evaluation,


                "actions":[]

            }




        actions = self.corrector.create(

            evaluation

        )



        return {


            "approved":

                False,


            "evaluation":

                evaluation,


            "actions":

                actions

        }