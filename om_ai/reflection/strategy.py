"""
OM Strategy Improvement Storage
"""


from pathlib import Path

import json





class StrategyMemory:



    def __init__(

        self,

        path="data/om-memory/strategies.json"

    ):


        self.path=Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )





    def save(

        self,

        strategy:dict

    ):


        data=[]



        if self.path.exists():

            data=json.loads(

                self.path.read_text()

            )



        data.append(strategy)



        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def load(self):


        if not self.path.exists():

            return []


        return json.loads(

            self.path.read_text()

        )