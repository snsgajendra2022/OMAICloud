"""
OM Code Change Model
"""


from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class CodeChange:


    file:str


    action:str


    description:str


    old_content:str = ""


    new_content:str = ""


    status:str = "planned"


    created_at:str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def to_dict(self):

        return {

            "file":
                self.file,

            "action":
                self.action,

            "description":
                self.description,

            "status":
                self.status,

            "created_at":
                self.created_at

        }