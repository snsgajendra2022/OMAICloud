"""
OM Long Term Memory
Permanent AI memory storage.
"""

from __future__ import annotations

import json
from pathlib import Path


class LongTermMemory:


    def __init__(
        self,
        path="storage/long_term_memory.json"
    ):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.memory=self.load()



    def load(self):

        if self.path.exists():

            return json.loads(
                self.path.read_text()
            )


        return {
            "facts":[],
            "preferences":[],
            "decisions":[]
        }



    def save(self):

        self.path.write_text(
            json.dumps(
                self.memory,
                indent=2
            )
        )



    def remember(
        self,
        category,
        value
    ):

        self.memory.setdefault(
            category,
            []
        ).append(value)

        self.save()



    def recall(
        self,
        category
    ):

        return self.memory.get(
            category,
            []
        )