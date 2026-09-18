"""Local-first wake-word detector (phrase match on transcript / energy gate)."""
from __future__ import annotations

import re
from typing import Any


class WakeWordEngine:
    """Detect configured wake phrase locally. Does not upload ambient audio."""

    def __init__(self, phrase: str = "hey om") -> None:
        self.set_phrase(phrase)
        self._armed = True

    def set_phrase(self, phrase: str) -> None:
        self.phrase = (phrase or "hey om").strip().lower()
        escaped = re.escape(self.phrase)
        self._pattern = re.compile(rf"\b{escaped}\b", re.I)
        # Fuzzy hey/hi/ok om aliases only for the default wake family.
        self._fuzzy_default = self.phrase in {"hey om", "hi om", "hello om", "ok om", "okay om"}

    def arm(self) -> None:
        self._armed = True

    def disarm(self) -> None:
        self._armed = False

    def detect_text(self, text: str) -> dict[str, Any]:
        if not self._armed:
            return {"detected": False, "armed": False, "phrase": self.phrase}
        low = (text or "").strip().lower()
        hit = bool(self._pattern.search(low))
        if not hit and self._fuzzy_default:
            hit = "om" in low.split()[:3] and any(
                w in low for w in ("hey", "hi", "hello", "okay", "ok")
            )
        return {
            "detected": hit,
            "armed": self._armed,
            "phrase": self.phrase,
            "matched_text": low[:120] if hit else "",
        }

    def status(self) -> dict[str, Any]:
        return {"phrase": self.phrase, "armed": self._armed, "mode": "local_phrase"}
