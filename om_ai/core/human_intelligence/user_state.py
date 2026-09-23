"""User state — live companion state for the human."""
from __future__ import annotations

from typing import Any


class UserState:
    def __init__(self) -> None:
        self._state: dict[str, Any] = {
            "mood": "neutral",
            "energy": "normal",
            "topic": "general",
            "intent": "conversation",
            "bond": "brother",
            "name": "",
        }

    def update(self, *, emotion: str = "", topic: str = "", intent: str = "", name: str = "", **extra: Any) -> dict[str, Any]:
        if emotion:
            self._state["mood"] = emotion
            if emotion in {"tired", "fatigue", "sad", "disappointed"}:
                self._state["energy"] = "low"
            elif emotion in {"excited", "happy", "angry"}:
                self._state["energy"] = "high"
            else:
                self._state["energy"] = "normal"
        if topic:
            self._state["topic"] = topic
        if intent:
            self._state["intent"] = intent
        if name:
            self._state["name"] = name
        self._state.update(extra)
        return dict(self._state)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._state)
