from __future__ import annotations


from datetime import datetime

import hashlib



class ProvenanceManager:


    def create(
        self,
        question,
        teachers,
        metadata=None
    ):


        raw = (

            question

            +

            "".join(
                teachers
            )

        )


        provenance_id = hashlib.sha256(

            raw.encode()

        ).hexdigest()[:20]



        return {


            "provenance_id":

                provenance_id,


            "question":

                question,


            "teachers":

                teachers,


            "created_at":

                datetime.utcnow()
                .isoformat(),


            "metadata":

                metadata or {}

        }