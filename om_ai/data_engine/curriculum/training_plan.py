"""
OM Training Plan

Creates SFT/DPO roadmap.
"""





class TrainingPlan:



    def generate(

        self,

        schedule:list[dict]

    ):


        return {


            "strategy":

                "progressive_training",



            "stages":

                schedule,



            "methods":

                [

                    "SFT",

                    "Evaluation",

                    "DPO"

                ]

        }