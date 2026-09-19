"""Response planner."""
from __future__ import annotations

from typing import Any


class ResponsePlanner:
    def plan(self, message: str, *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
        steps = ["understand", "reason", "check", "improve", "answer"]
        return {
            "steps": steps,
            "goal": (policy or {}).get("policy") or "balanced_assist",
            "max_sentences": int((policy or {}).get("max_sentences") or 3),
            "message_preview": (message or "")[:120],
        }
