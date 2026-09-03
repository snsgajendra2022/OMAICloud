"""
OM Physical Experience Memory
"""


from pathlib import Path

import json



class PhysicalMemory:


    def __init__(self):


        self.path = Path(

            "data/om-memory/physical_reasoning.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                "[]"

            )



    def store(

        self,

        data

    ):


        items=json.loads(

            self.path.read_text()

        )


        items.append(

            data

        )


        self.path.write_text(

            json.dumps(

                items,

                indent=2

            )

        )