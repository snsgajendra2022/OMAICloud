from .models import Relation


class RelationGenerator:


    def create(
        self,
        entities,
        source
    ):


        relations=[]


        for i in range(
            len(entities)-1
        ):

            relations.append(

                Relation(

                    subject=
                    entities[i].name,


                    relation=
                    "related_to",


                    object=
                    entities[i+1].name,


                    source=source

                )

            )


        return relations