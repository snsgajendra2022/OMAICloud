"""Conversation state — rolling semantic state across turns."""
from __future__ import annotations

from typing import Any


class ConversationState:
    def __init__(self) -> None:
        self._state: dict[str, Any] = {
            "topic": "general",
            "last_intent": "conversation",
            "last_goal": "continue",
            "open_question": None,
            "awaiting_permission": False,
            "turn": 0,
            "entities": [],
            "thread": [],
        }

    def update(self, frame: dict[str, Any] | None = None) -> dict[str, Any]:
        frame = frame or {}
        self._state["turn"] = int(self._state.get("turn") or 0) + 1
        intent = str(frame.get("intent") or self._state["last_intent"])
        goal = str(frame.get("goal") or self._state["last_goal"])
        self._state["last_intent"] = intent
        self._state["last_goal"] = goal

        topics = frame.get("topics") or []
        if topics:
            self._state["topic"] = topics[0]
        elif frame.get("topic"):
            self._state["topic"] = frame["topic"]

        ents = list(frame.get("entities") or [])
        if ents:
            merged = list(dict.fromkeys(list(self._state.get("entities") or []) + ents))
            self._state["entities"] = merged[-20:]

        text = str(frame.get("corrected") or frame.get("text") or "")[:160]
        if text:
            thread = list(self._state.get("thread") or [])
            thread.append({"role": "user", "text": text, "intent": intent})
            self._state["thread"] = thread[-12:]

        if frame.get("needs_clarification"):
            self._state["open_question"] = frame.get("clarify_ask") or "Need a bit more."
        elif intent not in {"followup"}:
            self._state["open_question"] = None

        self._state["awaiting_permission"] = bool(frame.get("awaiting_permission"))
        return self.snapshot()

    def remember_assistant(self, text: str) -> None:
        thread = list(self._state.get("thread") or [])
        thread.append({"role": "assistant", "text": (text or "")[:160]})
        self._state["thread"] = thread[-12:]

    def snapshot(self) -> dict[str, Any]:
        return dict(self._state)

    def reset(self) -> None:
        self.__init__()
