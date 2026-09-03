"""
OM Personal Knowledge Entity
"""


from dataclasses import dataclass





@dataclass
class PersonalEntity:


    name:str


    entity_type:str


    relation:str


    value:str



    def to_dict(self):

        return {

            "name":

                self.name,

            "type":

                self.entity_type,

            "relation":

                self.relation,

            "value":

                self.value

        }