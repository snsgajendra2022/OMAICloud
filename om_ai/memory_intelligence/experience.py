"""
OM Experience Memory Model
"""


from dataclasses import dataclass, field

from datetime import datetime



@dataclass
class Experience:


    type: str


    content: dict


    importance: float = 0.0


    created_at: str = field(

        default_factory=lambda:

        datetime.utcnow().isoformat()

    )



    def to_dict(self):

        return {

            "type":
                self.type,

            "content":
                self.content,

            "importance":
                self.importance,

            "created_at":
                self.created_at

        }