"""
OM Robot Intelligence Model
"""


from dataclasses import dataclass, field



@dataclass
class Robot:


    name:str


    robot_type:str


    sensors:list = field(
        default_factory=list
    )


    capabilities:list = field(
        default_factory=list
    )


    status:str="offline"



    def to_dict(self):

        return {

            "name":
                self.name,

            "type":
                self.robot_type,

            "sensors":
                self.sensors,

            "capabilities":
                self.capabilities,

            "status":
                self.status

        }