"""
OM Preference Dataset Generator

Used for DPO/RLHF style training.
"""


class PreferenceGenerator:



    def create(

        self,

        prompt,

        better,

        worse

    ):


        return {


            "prompt":

                prompt,


            "chosen":

                better,


            "rejected":

                worse

        }