"""
OM Model Version Registry
"""


from pathlib import Path

import json





class ModelRegistry:



    def __init__(self):


        self.path=Path(

            "data/models/registry.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                "[]"

            )




    def register(

        self,

        model

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(model)


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )