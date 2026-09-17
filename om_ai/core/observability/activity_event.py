from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


from .activity_types import ActivityType



@dataclass
class ActivityEvent:


    type: ActivityType


    title: str


    description: str = ""


    agent: str = "om"


    metadata: dict[str,Any] = field(
        default_factory=dict
    )


    event_id: str = field(
        default_factory=lambda:
        str(uuid.uuid4())
    )


    timestamp: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )



    def to_dict(self):

        return {

            "event_id":
                self.event_id,

            "type":
                self.type.value,

            "title":
                self.title,

            "description":
                self.description,

            "agent":
                self.agent,

            "metadata":
                self.metadata,

            "timestamp":
                self.timestamp

        }