"""
OM Digital Twin Core
"""


class DigitalTwin:



    def __init__(self):


        self.entities={}



    def register(

        self,

        entity

    ):


        self.entities[

            entity.name

        ] = entity.to_dict()



    def get(

        self,

        name

    ):


        return self.entities.get(

            name

        )



    def all(self):


        return self.entities