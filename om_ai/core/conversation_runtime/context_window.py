"""Sliding conversational context window."""
from __future__ import annotations

from typing import Any


class ContextWindow:
    def __init__(self, max_chars: int = 6000) -> None:
        self.max_chars = max_chars
        self.topic: str = ""
        self.goals: list[str] = []
        self.open_questions: list[str] = []

    def set_topic(self, topic: str) -> None:
        self.topic = (topic or "").strip()[:200]

    def add_goal(self, goal: str) -> None:
        g = (goal or "").strip()
        if g and g not in self.goals:
            self.goals.append(g)
            self.goals = self.goals[-8:]

    def add_question(self, q: str) -> None:
        q = (q or "").strip()
        if q and q not in self.open_questions:
            self.open_questions.append(q)
            self.open_questions = self.open_questions[-6:]

    def blob(self, history: list[dict[str, Any]]) -> str:
        parts = []
        if self.topic:
            parts.append(f"Current topic: {self.topic}")
        if self.goals:
            parts.append("Goals: " + "; ".join(self.goals[-3:]))
        if self.open_questions:
            parts.append("Open: " + "; ".join(self.open_questions[-2:]))
        for h in history[-10:]:
            parts.append(f"{h.get('role')}: {str(h.get('text') or '')[:400]}")
        out = "\n".join(parts)
        return out[: self.max_chars]

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "goals": list(self.goals),
            "open_questions": list(self.open_questions),
        }
