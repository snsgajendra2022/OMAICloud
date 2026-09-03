"""
OM Persistent Goal Storage
"""


from pathlib import Path

import json





class GoalStorage:



    def __init__(

        self,

        path="data/om-goals/goals.json"

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




    def load(self):


        return json.loads(

            self.path.read_text()

        )





    def save(

        self,

        goals

    ):


        self.path.write_text(

            json.dumps(

                goals,

                indent=2

            )

        )



    def add(

        self,

        goal

    ):


        data=self.load()


        data.append(

            goal

        )


        self.save(

            data

        )


        return goal