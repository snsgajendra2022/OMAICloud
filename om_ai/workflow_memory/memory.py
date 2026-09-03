"""
OM Workflow Experience Memory
"""


from dataclasses import dataclass, field

from datetime import datetime



@dataclass
class WorkflowExperience:


    goal: str


    workflow: list = field(
        default_factory=list
    )


    success: bool = False


    score: float = 0.0


    lessons: list = field(
        default_factory=list
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def to_dict(self):

        return {

            "goal":
                self.goal,

            "workflow":
                self.workflow,

            "success":
                self.success,

            "score":
                self.score,

            "lessons":
                self.lessons,

            "created_at":
                self.created_at

        }