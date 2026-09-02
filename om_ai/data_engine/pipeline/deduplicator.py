"""
OM Data Engine
Duplicate Removal
"""

from __future__ import annotations

from hashlib import sha256



class Deduplicator:


    def __init__(self):

        self.seen = set()



    def fingerprint(
        self,
        text: str
    ) -> str:


        normalized = text.lower().strip()


        return sha256(
            normalized.encode(
                "utf-8"
            )
        ).hexdigest()



    def is_duplicate(
        self,
        text: str
    ) -> bool:


        key = self.fingerprint(
            text
        )


        if key in self.seen:

            return True


        self.seen.add(
            key
        )


        return False



    def reset(self):

        self.seen.clear()