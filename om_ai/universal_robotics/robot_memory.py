"""
OM Universal Robot Memory
"""


from pathlib import Path

import json



class RobotMemory:



    def __init__(self):

        self.path = Path(

            "data/om-memory/robot_skills.json"

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

        item

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(item)


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )