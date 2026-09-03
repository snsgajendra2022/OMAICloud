"""
OM Local Knowledge Graph Storage
"""


from pathlib import Path

import json





class GraphStore:



    def __init__(

        self,

        path="data/om-knowledge/graph.json"

    ):


        self.path=Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        if not self.path.exists():

            self.path.write_text(

                json.dumps(

                    {

                        "entities":[],

                        "relations":[]

                    }

                )

            )





    def load(self):


        return json.loads(

            self.path.read_text()

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





    def add(

        self,

        graph

    ):


        data=self.load()


        for entity in graph["entities"]:


            value=entity.to_dict()


            if value not in data["entities"]:

                data["entities"].append(
                    value
                )



        for relation in graph["relations"]:


            value=relation.to_dict()


            if value not in data["relations"]:

                data["relations"].append(
                    value
                )


        self.save(data)


        return data