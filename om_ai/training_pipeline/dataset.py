"""
OM Training Dataset Storage
"""


from pathlib import Path

import json




class DatasetManager:



    def __init__(self):


        self.path = Path(

            "data/training/om_dataset.jsonl"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )




    def add(

        self,

        item

    ):


        with self.path.open(

            "a",

            encoding="utf-8"

        ) as file:


            file.write(

                json.dumps(item)

                +

                "\n"

            )




    def load(self):


        if not self.path.exists():

            return []


        return [

            json.loads(line)

            for line in self.path.read_text()

            .splitlines()

        ]