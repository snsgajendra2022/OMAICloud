"""Feedback from user / quality signals."""
from __future__ import annotations

import time
from typing import Any


class FeedbackEngine:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(
        self,
        *,
        user_message: str,
        answer: str,
        rating: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        ev = {
            "ts": time.time(),
            "user": (user_message or "")[:300],
            "answer": (answer or "")[:300],
            "rating": rating,  # good | bad | meh
            "note": note[:200],
        }
        self.events.append(ev)
        self.events = self.events[-200:]
        return ev
