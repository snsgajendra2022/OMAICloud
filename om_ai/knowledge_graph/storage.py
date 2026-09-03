"""
OM Knowledge Graph Storage
"""


from pathlib import Path

import json





class GraphStorage:



    def __init__(self):


        self.path = Path(

            "data/om-memory/knowledge_graph.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        if not self.path.exists():

            self.path.write_text(

                '{"entities":[],"relations":[]}'

            )




    def save(

        self,

        graph

    ):


        self.path.write_text(

            json.dumps(

                graph,

                indent=2

            )

        )



    def load(self):


        return json.loads(

            self.path.read_text()

        )