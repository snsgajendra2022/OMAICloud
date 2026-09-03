"""
OM Personal Knowledge Graph Storage
"""


from pathlib import Path

import json





class PersonalGraph:



    def __init__(

        self,

        path="data/om-user/profile_graph.json"

    ):


        self.path=Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                json.dumps([])

            )




    def add(

        self,

        entity

    ):


        data=json.loads(

            self.path.read_text()

        )


        if entity not in data:

            data.append(

                entity

            )


        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )



    def search(

        self,

        keyword

    ):


        data=json.loads(

            self.path.read_text()

        )


        return [

            item

            for item in data

            if keyword.lower()

            in str(item).lower()

        ]