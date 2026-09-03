"""
OM SFT Dataset Writer

Stores training examples as JSONL.
"""


from pathlib import Path

import json





class DatasetWriter:



    def __init__(

        self,

        path="data/om-training/sft.jsonl"

    ):


        self.path = Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )




    def append(

        self,

        example

    ):


        with self.path.open(

            "a",

            encoding="utf-8"

        ) as file:


            file.write(

                json.dumps(

                    example.to_dict(),

                    ensure_ascii=False

                )

                +

                "\n"

            )



        return True