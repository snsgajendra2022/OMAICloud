"""Emotional support route — warm, human replies for production brain."""
from __future__ import annotations

from typing import Any

from .conversation_engine import ConversationEngine


class EmotionalEngine:
    """Supportive conversation for stress / sadness / overwhelm turns."""

    def __init__(self) -> None:
        self.conversation = ConversationEngine()

    def respond(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> str:
        context = context or {}
        text = (message or "").strip()
        user_name = str(context.get("user_name") or context.get("name") or "")

        emotion = "neutral"
        try:
            from om_ai.core.emotion_intelligence.emotion_engine import EmotionEngine

            pack = EmotionEngine().analyze(text)
            emotion = str(pack.get("emotion") or "neutral")
        except Exception:
            low = text.lower()
            if any(k in low for k in ("sad", "depressed", "lonely", "cry")):
                emotion = "sad"
            elif any(k in low for k in ("stress", "anxious", "overwhelm", "panic")):
                emotion = "stressed"
            elif any(k in low for k in ("tired", "exhausted", "burnout")):
                emotion = "tired"
            elif any(k in low for k in ("frustrat", "angry", "annoyed")):
                emotion = "frustrated"

        try:
            base = self.conversation.respond(emotion, user_name=user_name)
            if base and base.strip():
                return base.strip()
        except Exception:
            pass

        name = f" {user_name}" if user_name else ""
        if emotion in {"sad", "stressed", "tired", "frustrated", "fatigue", "masked_stress"}:
            return (
                f"I'm here with you{name}. That sounds heavy — "
                "you don't have to carry it alone. "
                "Want to talk it through, or take one small next step together?"
            )
        return (
            f"I'm listening{name}. Tell me what's on your mind — "
            "I'm here for you."
        )
