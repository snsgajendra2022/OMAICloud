"""Speech context from history + current partial."""
from __future__ import annotations

from typing import Any


class SpeechContext:
    def build(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        previous_topic: str = "",
    ) -> dict[str, Any]:
        hist = history or []
        last_user = ""
        last_assistant = ""
        for turn in reversed(hist[-8:]):
            role = str(turn.get("role") or "")
            content = str(turn.get("content") or turn.get("text") or "").strip()
            if role == "assistant" and not last_assistant:
                last_assistant = content
            if role == "user" and not last_user:
                last_user = content
            if last_user and last_assistant:
                break
        return {
            "current": (text or "").strip(),
            "last_user": last_user,
            "last_assistant": last_assistant,
            "turns": len(hist),
            "topic_hint": previous_topic or "",
            "is_followup": bool(last_assistant) and len((text or "").split()) <= 8,
        }
