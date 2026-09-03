"""
OM Agent Communication Message
"""


from dataclasses import dataclass, field

from datetime import datetime




@dataclass
class AgentMessage:


    sender: str


    receiver: str


    message: str


    message_type: str = "information"


    metadata: dict = field(
        default_factory=dict
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def to_dict(self):

        return {

            "sender":
                self.sender,

            "receiver":
                self.receiver,

            "message":
                self.message,

            "type":
                self.message_type,

            "metadata":
                self.metadata,

            "created_at":
                self.created_at

        }