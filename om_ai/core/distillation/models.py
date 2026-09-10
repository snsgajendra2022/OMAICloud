from __future__ import annotations


from dataclasses import dataclass, field

from datetime import datetime



@dataclass
class TeacherModel:

    name: str

    available: bool = False

    metadata: dict = field(
        default_factory=dict
    )



@dataclass
class TeacherResponse:

    question: str

    teacher: str

    response: str

    status: str = "success"


    timestamp: str = field(

        default_factory=lambda:

        datetime.utcnow()
        .isoformat()

    )


    latency_ms: float = 0.0


    metadata: dict = field(

        default_factory=dict

    )



@dataclass
class DistillationResult:


    question: str


    responses: list[TeacherResponse] = field(

        default_factory=list

    )


    approved: bool = False


    distilled_answer: str = ""


    metadata: dict = field(

        default_factory=dict

    )