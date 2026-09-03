"""
OM Pattern Storage

Local persistent learning memory.
"""


from pathlib import Path

import json





class PatternStore:



    def __init__(
        self,
        path="data/om-memory/patterns.json"
    ):


        self.path = Path(path)

        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        if not self.path.exists():

            self.path.write_text(
                "[]"
            )





    def save(
        self,
        experience
    ):


        data = self.load()


        data.append(

            experience.__dict__

        )


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