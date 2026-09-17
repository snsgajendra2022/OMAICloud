from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class UserActivity:


    user_id:str


    session_id:str


    events:list = field(
        default_factory=list
    )


    created_at:str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def add(
        self,
        event
    ):

        self.events.append(
            event
        )