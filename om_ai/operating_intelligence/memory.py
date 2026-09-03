"""
OM Global Intelligence Memory
"""


from pathlib import Path

import json



class OMMemory:



    def __init__(self):


        self.path = Path(

            "data/om-memory/system_memory.json"

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

        event

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(

            event

        )


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def read(self):


        return json.loads(

            self.path.read_text()

        )