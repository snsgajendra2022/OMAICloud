"""Derive conversational goals from intent."""
from __future__ import annotations

from typing import Any


class GoalEngine:
    _GOAL_MAP: dict[str, str] = {
        "greeting": "connect",
        "morning": "connect",
        "afternoon": "connect",
        "evening": "connect",
        "thanks": "acknowledge",
        "goodbye": "close",
        "identity": "introduce",
        "user_name": "recall_identity",
        "user_name_set": "remember_identity",
        "debugging": "resolve_issue",
        "coding": "implement",
        "explain": "inform",
        "compare": "inform",
        "howto": "guide",
        "followup": "continue_thread",
        "chat": "assist",
        "empty": "invite",
    }

    def infer(self, intent: str, *, followup: bool = False) -> str:
        if followup and intent in {"chat", "explain", "howto", "coding"}:
            return "continue_thread"
        return self._GOAL_MAP.get(intent, "assist")

    def to_dict(self, goal: str, *, priority: str = "normal") -> dict[str, Any]:
        return {"goal": goal, "priority": priority}
