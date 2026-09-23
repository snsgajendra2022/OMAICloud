"""STEP 71.1 — Human Meaning Engine.

Word ≠ Meaning.

"today was very difficult" is sharing, not a request to explain a problem.
"""
from __future__ import annotations

import re
from typing import Any

from .human_context_engine import HumanContextEngine
from .implicit_meaning import ImplicitMeaning


class HumanMeaningEngine:
    """Convert raw text into why / needs / response_style."""

    def __init__(self) -> None:
        self.ctx = HumanContextEngine()
        self.implicit = ImplicitMeaning()

    def understand(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        emotion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = (message or "").strip()
        emotion = emotion or {}
        pack = self.ctx.understand(message, history=history, emotion=emotion)
        implicit = pack.get("implicit") or self.implicit.infer(
            text, conversation=pack.get("conversation"), emotion=emotion
        )

        sharing = self._is_sharing(text, implicit=implicit, emotion=emotion)
        needs_listening = bool(
            sharing
            or pack.get("listen_first")
            or implicit.get("listen_first")
        )

        possible_emotion = list(implicit.get("possible") or [])
        label = str(emotion.get("emotion") or emotion.get("label") or "")
        if label and label not in possible_emotion and label != "neutral":
            possible_emotion.insert(0, label)
        if not possible_emotion and needs_listening:
            possible_emotion = ["stress", "tiredness", "frustration"]

        response_style = "supportive" if needs_listening else "balanced"
        if label in {"happy", "excited"}:
            response_style = "warm_share"
        elif label in {"angry", "frustrated"}:
            response_style = "steady_solidarity"

        natural_ask = (
            pack.get("natural_ask")
            or implicit.get("natural_ask")
            or (self._default_ask(text) if needs_listening else None)
        )

        meaning = {
            "user_is_sharing": sharing,
            "needs_listening": needs_listening,
            "possible_emotion": possible_emotion,
            "response_style": response_style,
            "situation": str(pack.get("topic") or "general"),
            "incomplete": bool((pack.get("incomplete") or {}).get("incomplete")),
            "implicit_label": implicit.get("label"),
        }

        return {
            "text": text,
            "said": text,
            "meaning": meaning,
            # flat aliases used by presence layer
            "user_is_sharing": sharing,
            "needs_listening": needs_listening,
            "possible_emotion": possible_emotion,
            "response_style": response_style,
            "why": "sharing_feelings" if sharing else (
                "requesting_help" if "?" in text else "continuing"
            ),
            "intention": "support" if needs_listening else "assist",
            "missing": (pack.get("incomplete") or {}).get("incomplete"),
            "situation": pack.get("topic"),
            "natural_ask": natural_ask,
            "pack": pack,
            "implicit": implicit,
        }

    def _is_sharing(
        self,
        text: str,
        *,
        implicit: dict[str, Any],
        emotion: dict[str, Any],
    ) -> bool:
        low = (text or "").lower()
        if implicit.get("listen_first") or implicit.get("label") in {
            "rough_day",
            "fatigue",
            "overload",
            "sleep_strain",
            "emotional_load",
            "failure",
        }:
            return True
        if re.search(
            r"(?i)\b("
            r"today was|day was|difficult|failed|i failed|disappointed|"
            r"rough|tough|stressed|tired|thak|udas|gussa|lonely|"
            r"i feel|feeling|had a bad|very hard"
            r")\b",
            low,
        ):
            # Sharing feel — not asking "how do I fix X" with a clear task
            if re.search(r"(?i)\b(how (do|can|to)|fix|error|debug|implement|code)\b", low):
                return False
            return True
        if emotion.get("emotion") in {
            "sad", "tired", "stressed", "frustrated", "angry", "disappointed"
        }:
            return len(low.split()) <= 16
        return False

    def _default_ask(self, text: str) -> str:
        low = (text or "").lower()
        if re.search(r"(?i)\bfail", low):
            return "That sounds disappointing. Do you want to talk about what went wrong?"
        if re.search(r"(?i)\b(difficult|rough|hard|tough|bad day)\b", low):
            return "It sounds like today was really heavy for you. What happened?"
        return "I'm here with you. Want to tell me more?"
