from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResponseState:
    user_message: str

    intent: str = "general"
    response_type: str = "conversation"

    plan: list[str] = field(default_factory=list)

    context: dict[str, Any] = field(default_factory=dict)

    draft: str = ""
    final: str = ""

    quality_score: float = 0.0

    approved: bool = False
    regenerate: bool = False

    issues: list[str] = field(default_factory=list)