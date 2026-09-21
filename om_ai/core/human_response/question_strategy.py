"""When to ask — one natural question, never FAQ lists."""
from __future__ import annotations

from typing import Any


class QuestionStrategy:
    def choose(
        self,
        *,
        intent: str,
        emotion: dict[str, Any] | None = None,
        meaning: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> dict[str, Any]:
        emotion = emotion or {}
        meaning = meaning or {}
        if intent not in {"ask", "clarify", "comfort"}:
            return {"ask": False, "question": None}
        label = str(emotion.get("emotion") or "")
        hi = locale == "hi"
        if label in {"sad", "stressed", "frustrated", "tired", "masked_stress"}:
            q = "Kya hua?" if hi else "What happened?"
        elif meaning.get("missing_information"):
            q = "Kaunsa hissa stuck hai?" if hi else "Which part is blocking you?"
        else:
            q = "Aur batao?" if hi else "Tell me more?"
        return {"ask": True, "question": q, "style": "gentle_single"}
