"""
OM Autonomous Goal Model
"""


from dataclasses import dataclass, field

from datetime import datetime



@dataclass
class Goal:


    id: str


    title: str


    description: str


    status: str = "active"


    progress: float = 0.0


    milestones: list = field(
        default_factory=list
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def update_progress(

        self,

        value:float

    ):

        self.progress = min(
            1.0,
            value
        )



    def to_dict(self):

        return {

            "id":
                self.id,

            "title":
                self.title,

            "description":
                self.description,

            "status":
                self.status,

            "progress":
                self.progress,

            "milestones":
                self.milestones,

            "created_at":
                self.created_at

        }