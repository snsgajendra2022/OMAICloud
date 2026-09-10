from __future__ import annotations

from pathlib import Path

import json



class KnowledgeWriter:


    def __init__(
        self,
        path="data/knowledge/distilled"
    ):


        self.path = Path(
            path
        )

        self.path.mkdir(

            parents=True,

            exist_ok=True

        )



    def save(
        self,
        knowledge
    ):


        file = (

            self.path

            /

            f"{knowledge.knowledge_id}.json"

        )


        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:


            json.dump(

                knowledge.__dict__,

                f,

                indent=2,

                ensure_ascii=False

            )


        return str(file)



    def load(
        self,
        knowledge_id
    ):


        file = (

            self.path

            /

            f"{knowledge_id}.json"

        )


        if not file.exists():

            return None


        with open(
            file,
            encoding="utf-8"
        ) as f:


            return json.load(f)