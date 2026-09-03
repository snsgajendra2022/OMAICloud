"""
OM Failure Event Model
"""


from dataclasses import dataclass, field

from datetime import datetime



@dataclass
class FailureEvent:


    task: str


    error: str


    agent: str = ""


    severity: str = "medium"


    attempts: int = 0


    created_at: str = field(

        default_factory=lambda:

        datetime.utcnow().isoformat()

    )



    def to_dict(self):

        return {

            "task":

                self.task,

            "error":

                self.error,

            "agent":

                self.agent,

            "severity":

                self.severity,

            "attempts":

                self.attempts,

            "created_at":

                self.created_at

        }