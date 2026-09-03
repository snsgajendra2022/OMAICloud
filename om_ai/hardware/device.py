"""
OM Hardware Device Model
"""


from dataclasses import dataclass, field



@dataclass
class HardwareDevice:


    name: str


    device_type: str


    manufacturer: str = ""


    capabilities: list = field(

        default_factory=list

    )


    status: str = "offline"



    def to_dict(self):

        return {


            "name":

                self.name,


            "type":

                self.device_type,


            "manufacturer":

                self.manufacturer,


            "capabilities":

                self.capabilities,


            "status":

                self.status

        }