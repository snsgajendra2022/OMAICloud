from __future__ import annotations


import json

from pathlib import Path



class GraphStorage:
    """
    Persistent storage for OM graph.
    """


    def save(
        self,
        graph,
        path: str
    ):

        file = Path(path)

        file.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        file.write_text(

            json.dumps(
                graph.export(),
                indent=2,
                ensure_ascii=False
            ),

            encoding="utf-8"

        )



    def load(
        self,
        path: str
    ):

        file = Path(path)


        if not file.exists():

            return None


        return json.loads(

            file.read_text(
                encoding="utf-8"
            )

        )