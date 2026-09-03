"""
OM Weakness Detection Engine
"""


class WeaknessDetector:



    def detect(

        self,

        analysis

    ):


        weaknesses=[]



        if analysis.get(

            "performance_score",

            0

        ) < 0.8:


            weaknesses.append(

                "low_quality_output"

            )



        return {


            "weaknesses":

                weaknesses,


            "count":

                len(weaknesses)

        }