"""
OM Model Definition

Represents model versions and capabilities.
"""


from dataclasses import dataclass, field

from datetime import datetime




@dataclass
class OMModel:


    name:str


    version:str


    model_type:str


    parameters:str = ""


    status:str = "created"


    capabilities:list = field(

        default_factory=list

    )


    created_at:str = field(

        default_factory=lambda:

        datetime.utcnow().isoformat()

    )



    def to_dict(self):

        return {


            "name":

                self.name,


            "version":

                self.version,


            "model_type":

                self.model_type,


            "parameters":

                self.parameters,


            "status":

                self.status,


            "capabilities":

                self.capabilities,


            "created_at":

                self.created_at

        }