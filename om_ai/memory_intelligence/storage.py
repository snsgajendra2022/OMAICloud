"""
OM Permanent Experience Storage
"""


from pathlib import Path

import json





class ExperienceStorage:



    def __init__(

        self,

        path="data/om-memory/consolidated.json"

    ):


        self.path=Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )




        if not self.path.exists():

            self.path.write_text(

                "[]"

            )




    def add(

        self,

        item:dict

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(

            item

        )


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def all(self):


        return json.loads(

            self.path.read_text()

        )