"""
Emotional intelligence facade — text + voice cues + conversation context.

Reuses om_ai.core.emotion_intelligence (no duplicate detectors).
"""
from __future__ import annotations

from typing import Any

from om_ai.core.emotion_intelligence import EmotionEngine


class EmotionalIntelligence:
    def __init__(self) -> None:
        self.engine = EmotionEngine()

    def analyze(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        voice_cues: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pack = self.engine.analyze(text, history=history)
        cues = voice_cues or {}
        # Voice cues can raise caution even when text says "I'm fine"
        if cues.get("hesitation") or cues.get("slow") or float(cues.get("silence_ms") or 0) > 800:
            if str(pack.get("emotion") or "") in {"neutral", "happy"} and self._masked_fine(text):
                pack = {
                    **pack,
                    "emotion": "masked_stress",
                    "label": "masked_stress",
                    "need": "listen_first",
                    "conversation_need": "listen_first",
                    "response_style": "gentle",
                    "masked": True,
                    "voice_adjusted": True,
                }
        else:
            pack = {
                **pack,
                "conversation_need": pack.get("need") or "steady",
            }
        if "conversation_need" not in pack:
            pack["conversation_need"] = pack.get("need") or "steady"
        return {
            "emotion": pack.get("emotion") or pack.get("label") or "neutral",
            "confidence": pack.get("confidence") or 0.55,
            "response_style": pack.get("response_style") or "steady",
            "conversation_need": pack.get("conversation_need") or pack.get("need") or "steady",
            "pack": pack,
        }

    @staticmethod
    def _masked_fine(text: str) -> bool:
        low = (text or "").lower().strip()
        return low in {"i'm fine", "im fine", "i am fine", "fine", "theek hun", "theek hoon", "sab theek"}


_EI: EmotionalIntelligence | None = None


def get_emotional_intelligence() -> EmotionalIntelligence:
    global _EI
    if _EI is None:
        _EI = EmotionalIntelligence()
    return _EI
