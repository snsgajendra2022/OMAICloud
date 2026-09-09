from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Experience:


    input_message: str


    response: str


    result: str = "unknown"


    score: float = 0.0


    metadata: dict = field(
        default_factory=dict
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )