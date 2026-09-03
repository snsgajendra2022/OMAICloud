"""
OM Repository Knowledge Index
"""


import json

from pathlib import Path





class CodeIndex:



    def __init__(self):


        self.path=Path(

            "data/om-code/index.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        if not self.path.exists():

            self.path.write_text(

                "{}"

            )




    def save(

        self,

        data

    ):


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def load(self):


        return json.loads(

            self.path.read_text()

        )