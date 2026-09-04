from .models import Entity


class EntityGenerator:


    def create(
        self,
        extracted_data,
        source
    ):

        entities=[]


        for key,value in extracted_data.items():

            entities.append(

                Entity(

                    name=str(value),

                    entity_type=key,

                    source=source

                )

            )


        return entities