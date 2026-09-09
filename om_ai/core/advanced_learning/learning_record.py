from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LearningRecord:


    input_data: str


    output_data: str


    feedback: str = ""


    learned_patterns: list = field(
        default_factory=list
    )


    improvements: list = field(
        default_factory=list
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )