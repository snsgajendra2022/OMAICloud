from __future__ import annotations
from typing import Any


class GoalUnderstanding:
    """Turn intentions into explicit goals."""

    def parse(self, intention: dict[str, Any], text: str) -> dict[str, Any]:
        intent = intention.get("intent") or "converse"
        goals = {
            "emotional_support": "Support the user emotionally and invite them to share.",
            "inspect_screen": "Inspect the screen / environment and explain what is wrong.",
            "create_reminder": "Capture a reminder with time and task.",
            "diagnose_and_plan": "Diagnose the stated problem and propose a step-by-step plan.",
            "greeting": "Greet warmly and signal readiness.",
            "converse": "Continue natural conversation as a personal companion.",
        }
        return {
            "goal": goals.get(intent, goals["converse"]),
            "intent": intent,
            "user_ask": text,
            "success_criteria": "User feels understood and next action is clear.",
        }
