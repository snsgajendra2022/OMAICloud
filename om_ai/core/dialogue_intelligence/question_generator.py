"""Question generator — one natural question when useful."""
from __future__ import annotations

from typing import Any


class QuestionGenerator:
    def generate(
        self,
        *,
        human: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> str | None:
        human = human or {}
        emotion = emotion or {}
        if human.get("natural_ask"):
            return str(human["natural_ask"])
        if emotion.get("need") == "listen_first":
            return (
                "Kya hua tha?"
                if locale == "hi"
                else "What felt hardest about it?"
            )
        return None
