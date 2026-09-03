"""
OM Digital Twin Entity Model
"""


from dataclasses import dataclass, field



@dataclass
class DigitalEntity:


    name:str


    entity_type:str


    properties:dict = field(

        default_factory=dict

    )


    relationships:list = field(

        default_factory=list

    )


    def to_dict(self):

        return {


            "name":

                self.name,


            "type":

                self.entity_type,


            "properties":

                self.properties,


            "relationships":

                self.relationships

        }