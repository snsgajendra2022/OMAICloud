"""Propose offline improvement events (never mutates weights live)."""
from __future__ import annotations

from typing import Any

from .failure_memory import FailureMemory
from .skill_gap_detector import SkillGapDetector


class ImprovementEngine:
    def __init__(self) -> None:
        self.failures = FailureMemory()
        self.gaps = SkillGapDetector()
        self.queue: list[dict[str, Any]] = []

    def observe(self, *, user_message: str, answer: str, feedback: dict[str, Any] | None = None) -> dict[str, Any]:
        gap = self.gaps.detect(user_message, answer)
        event = {
            "type": "learning_event",
            "gaps": gap.get("gaps") or [],
            "feedback": feedback or {},
            "user": (user_message or "")[:200],
            "answer": (answer or "")[:200],
        }
        if gap.get("has_gap") or (feedback or {}).get("rating") == "bad":
            self.failures.remember(
                kind=",".join(gap.get("gaps") or ["user_feedback"]),
                detail=(feedback or {}).get("note") or answer[:200],
                user_message=user_message,
            )
            self.queue.append(event)
            self.queue = self.queue[-100:]
        return {"queued": bool(gap.get("has_gap") or (feedback or {}).get("rating") == "bad"), "event": event}
