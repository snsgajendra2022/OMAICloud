"""
OM Fine Tuning Controller

Future:

PyTorch
Transformers
Accelerate
"""


class FineTuneManager:



    def start(

        self,

        model,

        dataset,

        config=None

    ):


        return {


            "status":

                "queued",


            "model":

                model,


            "samples":

                len(dataset),


            "config":

                config or {}

        }