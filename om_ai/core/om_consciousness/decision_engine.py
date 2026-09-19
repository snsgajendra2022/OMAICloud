from __future__ import annotations
from typing import Any


class DecisionEngine:
    """Decide which subsystem should own the reply."""

    def decide(self, goal: dict[str, Any]) -> dict[str, Any]:
        intent = goal.get("intent") or "converse"
        route = {
            "emotional_support": "brain",
            "greeting": "brain",
            "create_reminder": "language_intelligence",
            "inspect_screen": "vision",
            "diagnose_and_plan": "action_engine",
            "converse": "brain",
        }.get(intent, "brain")
        return {"route": route, "intent": intent, "plan_first": intent == "diagnose_and_plan"}
