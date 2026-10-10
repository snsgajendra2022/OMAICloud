from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GenerationResult:
    text: str
    success: bool
    quality: float = 0.0
    attempts: int = 1
    rejected: bool = False
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)