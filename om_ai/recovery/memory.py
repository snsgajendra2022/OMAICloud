"""
OM Failure Learning Memory
"""


from pathlib import Path

import json




class FailureMemory:



    def __init__(self):


        self.path = Path(

            "data/om-memory/failures.json"

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

        failure

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(

            failure

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