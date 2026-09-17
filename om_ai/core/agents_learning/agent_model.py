from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentCapability:

    name: str

    skills: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )



@dataclass
class AgentResult:

    agent: str

    success: bool

    output: Any

    confidence: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )