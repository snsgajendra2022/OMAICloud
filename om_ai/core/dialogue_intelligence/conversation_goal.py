"""Conversation goal for the current thread."""
from __future__ import annotations

from typing import Any


class ConversationGoal:
    def infer(
        self,
        message: str,
        *,
        human: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        is_action: bool = False,
    ) -> dict[str, Any]:
        human = human or {}
        emotion = emotion or {}
        if is_action:
            return {"goal": "execute", "priority": "action"}
        if human.get("incomplete", {}).get("incomplete"):
            return {"goal": "continue_thread", "priority": "listen"}
        if emotion.get("need") == "listen_first" or human.get("listen_first"):
            return {"goal": "support", "priority": "listen"}
        if (human.get("conversation") or {}).get("celebration"):
            return {"goal": "celebrate", "priority": "encourage"}
        if (human.get("conversation") or {}).get("is_question"):
            return {"goal": "answer", "priority": "explain"}
        if (human.get("implicit") or {}).get("has_implicit"):
            return {"goal": "explore", "priority": "ask"}
        return {"goal": "assist", "priority": "answer"}
