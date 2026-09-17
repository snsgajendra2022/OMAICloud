from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .event_types import ActivityType



@dataclass
class ActivityEvent:


    event_type: ActivityType


    message: str


    agent: str = "om"


    metadata: dict[str,Any] = field(
        default_factory=dict
    )


    timestamp:str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )