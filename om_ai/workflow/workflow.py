"""
OM Workflow Model

Represents a complete autonomous process.
"""


from dataclasses import dataclass, field
from datetime import datetime



@dataclass
class Workflow:


    id: str


    goal: str


    status: str = "created"


    tasks: list = field(
        default_factory=list
    )


    progress: float = 0.0


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def update_progress(self):

        if not self.tasks:

            self.progress = 0

            return


        completed = len(

            [

                task

                for task in self.tasks

                if task.get("status")
                == "completed"

            ]

        )


        self.progress = round(

            completed / len(self.tasks),

            2

        )



    def to_dict(self):

        return {

            "id":
                self.id,

            "goal":
                self.goal,

            "status":
                self.status,

            "tasks":
                self.tasks,

            "progress":
                self.progress,

            "created_at":
                self.created_at

        }