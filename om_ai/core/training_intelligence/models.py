from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TrainingQuestion:

    question: str

    domain: str

    difficulty: str = "unknown"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



@dataclass
class TeacherResponse:

    teacher: str

    question: str

    answer: str

    score: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



@dataclass
class TrainingExample:

    instruction: str

    output: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



@dataclass
class ProvenanceRecord:

    id: str

    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )

    source: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class QualityResult:
    """
    Dynamic quality evaluation result.

    Used by:
    - Response evaluator
    - Self critic
    - Dataset filtering
    - Training approval
    """

    score: float

    approved: bool

    issues: list[str] = field(
        default_factory=list
    )

    dimensions: dict[str, float] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



@dataclass
class PreferenceExample:
    """
    DPO preference training example.

    Used for:

    Prompt
        |
        +--> chosen answer
        |
        +--> rejected answer

    The model learns preference quality.
    """

    prompt: str

    chosen: str

    rejected: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )