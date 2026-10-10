"""Emotion-aware support with uncertainty and crisis-safe escalation."""
from __future__ import annotations

import re
from typing import Any

from .conversation_engine import ConversationEngine


class EmotionalEngine:
    """Respond supportively without claiming certainty about inner feelings."""

    _CRISIS = re.compile(
        r"\b(i want to die|want to end my life|kill myself|suicidal|"
        r"thinking about suicide|hurt myself|self[- ]harm|can't go on living)\b",
        re.IGNORECASE,
    )

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
        user_name = str(context.get("user_name") or context.get("name") or "").strip()
        name = f" {user_name}" if user_name else ""

        # High-risk language takes precedence over ordinary sentiment handling.
        # This is a conservative phrase detector, not a clinical risk assessment.
        if self._CRISIS.search(text):
            return (
                f"I'm really sorry you're facing this{name}. I'm glad you told me. "
                "Are you in immediate danger right now, or have you taken steps to hurt yourself? "
                "If you may act on these thoughts, please contact your local emergency number now "
                "or go to the nearest emergency department, and if possible stay with a trusted "
                "person who can help keep you safe. I can stay with you while we focus on the next "
                "safe step."
            )

        emotion = "unknown"
        emotion_confidence = 0.0
        try:
            from om_ai.core.emotion_intelligence.emotion_engine import EmotionEngine

            pack = EmotionEngine().analyze(text)
            emotion = str(pack.get("emotion") or "unknown")
            try:
                emotion_confidence = float(pack.get("confidence") or 0.0)
            except (TypeError, ValueError):
                emotion_confidence = 0.0
        except Exception:
            low = text.casefold()
            cues = (
                ("sad", ("sad", "depressed", "lonely", "cry", "heartbroken")),
                ("stressed", ("stress", "anxious", "overwhelm", "panic", "worried")),
                ("tired", ("tired", "exhausted", "burnout", "drained")),
                ("frustrated", ("frustrat", "angry", "annoyed", "still not working")),
                ("positive", ("happy", "excited", "great news", "finally working")),
                ("confused", ("confused", "don't understand", "do not understand", "not clear")),
            )
            for label, phrases in cues:
                if any(phrase in low for phrase in phrases):
                    emotion = label
                    emotion_confidence = 0.45
                    break

        # Emotion models are not always calibrated; only use the label as a
        # gentle tone hint, never as a diagnosis or an assertion about the user.
        try:
            base = self.conversation.respond(emotion, user_name=user_name)
            if base and base.strip():
                return base.strip()
        except Exception:
            pass

        if emotion in {"sad", "stressed", "tired", "frustrated", "fatigue", "masked_stress"}:
            return (
                f"I'm sorry this feels difficult{name}. I may not have the full picture, "
                "but I can listen. Would you rather talk through what's happening, or work "
                "on one small next step together?"
            )
        if emotion == "confused":
            return "That's okay; we can slow down and take it one step at a time. Which part should we start with?"
        if emotion == "positive":
            return "That's great to hear! What would you like to do next?"
        return "I'm listening. What would be most helpful for you right now?"
