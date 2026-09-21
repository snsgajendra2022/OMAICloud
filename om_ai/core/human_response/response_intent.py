"""Map timing + emotion into a response intent (not the spoken words)."""
from __future__ import annotations

from typing import Any


class ResponseIntent:
    def resolve(
        self,
        *,
        timing_action: str,
        emotion: dict[str, Any] | None = None,
        meaning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        emotion = emotion or {}
        meaning = meaning or {}
        action = (timing_action or "answer").lower()
        need = str(emotion.get("conversation_need") or emotion.get("need") or "steady")
        intent = {
            "wait": "stay_silent",
            "listen": "stay_silent",
            "interrupt": "yield",
            "comfort": "comfort",
            "ask": "ask",
            "clarify": "clarify",
            "act": "give_action",
            "answer": "answer",
            "remember": "remember",
        }.get(action, "answer")
        if need in {"listen_first", "support_and_listen"} and intent == "answer":
            intent = "comfort"
        return {
            "intent": intent,
            "should_speak": intent not in {"stay_silent", "yield"},
            "should_ask": intent in {"ask", "clarify", "comfort"},
            "should_act": intent == "give_action",
            "emotion": emotion.get("emotion"),
            "goal": meaning.get("inferred_goal"),
        }
