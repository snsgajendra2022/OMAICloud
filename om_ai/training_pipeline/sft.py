"""
Supervised Fine Tuning Dataset Generator
"""


class SFTGenerator:



    def create(

        self,

        experience

    ):


        return {


            "instruction":

                experience["input"],


            "response":

                experience["output"]

        }