"""
OM Improvement Strategy Generator
"""


class ImprovementStrategy:



    def generate(

        self,

        weaknesses

    ):


        strategies=[]



        for item in weaknesses.get(

            "weaknesses",

            []

        ):


            if item == "low_quality_output":


                strategies.append(

                    "Improve reasoning validation"

                )



        return {


            "strategies":

                strategies

        }