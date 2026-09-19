from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OnboardingEvent:
    user_id: str
    event: str
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "event": self.event,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }
