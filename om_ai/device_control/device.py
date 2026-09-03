"""
OM Device Model
"""


from dataclasses import dataclass, field



@dataclass
class Device:


    name: str


    device_type: str


    location: str = ""


    status: str = "offline"


    capabilities: list = field(

        default_factory=list

    )


    def to_dict(self):

        return {

            "name":

                self.name,


            "type":

                self.device_type,


            "location":

                self.location,


            "status":

                self.status,


            "capabilities":

                self.capabilities

        }