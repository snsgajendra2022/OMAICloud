"""
OM Experience Model

Stores successful and failed executions.
"""


from dataclasses import dataclass, field

from datetime import datetime





@dataclass
class Experience:


    question: str


    answer: str


    score: float = 0.0


    success: bool = False


    category: str = "general"


    metadata: dict = field(
        default_factory=dict
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )