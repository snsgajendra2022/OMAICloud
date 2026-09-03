"""
OM Knowledge Graph Entity
"""


from dataclasses import dataclass



@dataclass
class Entity:


    name: str


    entity_type: str = "concept"


    metadata: dict = None



    def to_dict(self):

        return {

            "name": self.name,

            "type": self.entity_type,

            "metadata": self.metadata or {}

        }