"""
OM Physical Relationship Engine
"""


class RelationEngine:


    def understand(

        self,

        objects

    ):


        relations=[]


        for obj in objects:


            relations.append(

                {


                    "object":

                        obj,


                    "relation":

                        "connected"

                }

            )


        return {


            "relations":

                relations

        }