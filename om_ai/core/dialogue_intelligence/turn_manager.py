"""Turn manager — decide the move for this turn."""
from __future__ import annotations

from typing import Any


class TurnManager:
    def decide(self, goal: dict[str, Any], *, interrupted: bool = False) -> dict[str, Any]:
        if interrupted:
            return {"move": "yield", "action": "listen", "speak": False}
        priority = str(goal.get("priority") or "answer")
        mapping = {
            "listen": {"move": "listen", "action": "acknowledge_and_invite", "speak": True},
            "ask": {"move": "ask", "action": "one_gentle_question", "speak": True},
            "explain": {"move": "explain", "action": "answer_clearly", "speak": True},
            "encourage": {"move": "encourage", "action": "celebrate_then_ask", "speak": True},
            "action": {"move": "act", "action": "confirm_and_execute", "speak": True},
            "answer": {"move": "answer", "action": "direct_help", "speak": True},
        }
        return mapping.get(priority, mapping["answer"]) | {"goal": goal.get("goal")}
