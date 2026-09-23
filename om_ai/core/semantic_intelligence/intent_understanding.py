"""Intent understanding — semantic intent labels for a turn."""
from __future__ import annotations

import re
from typing import Any


class IntentUnderstanding:
    """Map corrected language → intent + confidence."""

    def understand(
        self,
        text: str,
        *,
        speech_act: str = "statement",
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        low = (text or "").lower().strip()
        hist = history or []

        if re.search(r"(?i)\b(search|google|khoj|research|look\s+up)\b", low):
            return self._pack("research", 0.9, speech_act="request")
        if re.search(r"(?i)\b(open|kholo|launch|start|delete|send|run)\b", low):
            return self._pack("action", 0.88, speech_act="request")
        if re.search(
            r"(?i)\b(today was|difficult|failed|tired|sad|stress|bad day|thak|udas)\b",
            low,
        ):
            return self._pack("sharing", 0.9, speech_act="share")
        if re.search(r"(?i)^\s*(hi|hello|hey|namaste|yo)\b", low):
            return self._pack("greeting", 0.95, speech_act="statement")
        if re.search(r"(?i)\b(thanks|thank you|shukriya|dhanyavad)\b", low):
            return self._pack("thanks", 0.92, speech_act="statement")
        if re.search(r"(?i)\b(joke|majaak|funny|haha|lol)\b", low):
            return self._pack("joke", 0.85, speech_act="request")
        if re.search(r"(?i)\b(fix|bug|debug|not working|crash|exception)\b", low):
            return self._pack("problem", 0.87, speech_act=speech_act or "request")
        if speech_act == "question" or "?" in (text or "") or re.search(
            r"(?i)\b(what|how|why|when|where|kaise|kya|kyun|explain)\b", low
        ):
            return self._pack("question", 0.84, speech_act="question")
        if re.search(r"(?i)\b(continue|us[ei]|wahi|pehle|keep going)\b", low) or (
            len(low.split()) <= 3 and hist
        ):
            return self._pack("followup", 0.75, speech_act="statement")
        if speech_act == "share":
            return self._pack("sharing", 0.8, speech_act="share")
        return self._pack("conversation", 0.6, speech_act=speech_act or "statement")

    def _pack(self, intent: str, confidence: float, *, speech_act: str) -> dict[str, Any]:
        return {
            "intent": intent,
            "confidence": confidence,
            "speech_act": speech_act,
            "label": intent,
        }
