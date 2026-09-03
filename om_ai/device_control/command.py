"""
OM Device Command System
"""


from dataclasses import dataclass





@dataclass
class DeviceCommand:


    device: str


    action: str


    parameters: dict



    def to_dict(self):

        return {


            "device":

                self.device,


            "action":

                self.action,


            "parameters":

                self.parameters

        }