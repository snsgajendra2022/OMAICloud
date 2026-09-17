from __future__ import annotations


import hashlib



class DuplicateDetector:


    def __init__(self):

        self.hashes=set()



    def fingerprint(
        self,
        item
    ):

        value = (

            item.instruction.strip()

            +

            item.output.strip()

        )


        return hashlib.sha256(

            value.encode(
                "utf-8"
            )

        ).hexdigest()



    def is_duplicate(
        self,
        item
    ):


        key = self.fingerprint(
            item
        )


        if key in self.hashes:

            return True


        self.hashes.add(
            key
        )


        return False