"""Wake word bridge."""
from __future__ import annotations

from typing import Any


class WakeWord:
    def detect(self, text: str, phrase: str = "hey om") -> dict[str, Any]:
        try:
            from om_ai.core.voice_intelligence.wake_word_engine import WakeWordEngine

            return WakeWordEngine(phrase).detect_text(text)
        except Exception:
            low = (text or "").lower()
            hit = any(w in low for w in ("hey om", "jarvis", "om"))
            return {"detected": hit, "phrase": phrase, "mode": "local_phrase"}
