"""
OM Knowledge Relationship
"""


from dataclasses import dataclass




@dataclass
class Relationship:


    source: str


    relation: str


    target: str



    def to_dict(self):

        return {


            "source":

                self.source,


            "relation":

                self.relation,


            "target":

                self.target

        }