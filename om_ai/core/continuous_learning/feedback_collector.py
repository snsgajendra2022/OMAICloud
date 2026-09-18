"""STEP 29 — Feedback collector."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class FeedbackEvent:
    message: str
    answer: str
    rating: float = 0.0
    reason: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "message": self.message[:500],
            "answer": self.answer[:1000],
            "rating": self.rating,
            "reason": self.reason,
            "created_at": self.created_at,
        }


class FeedbackCollector:
    def __init__(self) -> None:
        self._events: list[FeedbackEvent] = []

    def add(self, message: str, answer: str, *, rating: float = 0.0, reason: str = "") -> dict[str, Any]:
        ev = FeedbackEvent(message=message, answer=answer, rating=rating, reason=reason)
        self._events.append(ev)
        if len(self._events) > 500:
            self._events = self._events[-500:]
        return ev.to_dict()

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events[-limit:]]

    def negatives(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events if e.rating < 0.5 or e.reason]
