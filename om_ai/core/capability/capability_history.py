from __future__ import annotations

from datetime import datetime



class CapabilityHistory:
    """
    Stores capability evolution.
    """


    def __init__(self):

        self.records = []



    def add(
        self,
        snapshot
    ):

        self.records.append(

            {

                "time":
                    datetime.utcnow()
                    .isoformat(),

                "capabilities":
                    snapshot

            }

        )



    def get(self):

        return self.records