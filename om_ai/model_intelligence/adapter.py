"""
OM Model Adapter System

Future connection:

LoRA
QLoRA
Adapters
"""


class ModelAdapter:



    def prepare(

        self,

        model,

        dataset

    ):


        return {


            "model":

                model,


            "dataset_size":

                len(dataset),


            "adapter":

                "prepared"

        }