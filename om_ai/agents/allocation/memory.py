"""
OM Agent Performance Memory
"""


from pathlib import Path

import json





class AgentPerformanceMemory:



    def __init__(self):


        self.path = Path(

            "data/om-memory/agent_performance.json"

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

        result:dict

    ):


        data=json.loads(

            self.path.read_text()

        )


        data.append(result)



        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def get_all(self):


        return json.loads(

            self.path.read_text()

        )