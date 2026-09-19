"""Local-first wake-word detector.

Default: lightweight phrase gate on transcript (no always-on cloud upload).
Optional: Picovoice Porcupine if `pvporcupine` + `OM_WAKE_PORCUPINE_KEY` are set.
"""
from __future__ import annotations

import os
import re
from typing import Any


_DEFAULT_ALIASES = (
    "hey om",
    "hi om",
    "hello om",
    "ok om",
    "okay om",
    "om",
    "hey jarvis",
    "hi jarvis",
    "jarvis",
    "hey jarvice",  # common STT misspell
)


class WakeWordEngine:
    """Detect configured wake phrase locally. Does not upload ambient audio."""

    def __init__(self, phrase: str = "hey om") -> None:
        self._porcupine = None
        self._porcupine_err: str | None = None
        self.set_phrase(phrase)
        self._armed = True
        self._try_porcupine()

    def set_phrase(self, phrase: str) -> None:
        self.phrase = (phrase or "hey om").strip().lower() or "hey om"
        aliases = {self.phrase, *_DEFAULT_ALIASES}
        # Keep short single-token phrases only when they match the family
        self._aliases = tuple(sorted(aliases, key=len, reverse=True))
        parts = [re.escape(a) for a in self._aliases if a]
        self._pattern = re.compile(rf"\b(?:{'|'.join(parts)})\b", re.I)

    def _try_porcupine(self) -> None:
        """Optional ultra-light always-on engine — only if key + package present."""
        key = (os.getenv("OM_WAKE_PORCUPINE_KEY") or os.getenv("PICOVOICE_ACCESS_KEY") or "").strip()
        if not key or key.lower() in {"your_key_here", "changeme", "xxx", ""}:
            return
        try:
            import pvporcupine  # type: ignore

            keyword = (os.getenv("OM_WAKE_PORCUPINE_KEYWORD") or "jarvis").strip()
            self._porcupine = pvporcupine.create(
                access_key=key,
                keywords=[keyword],
            )
        except Exception as exc:
            self._porcupine = None
            self._porcupine_err = str(exc)[:200]

    def arm(self) -> None:
        self._armed = True

    def disarm(self) -> None:
        self._armed = False

    def detect_text(self, text: str) -> dict[str, Any]:
        if not self._armed:
            return {"detected": False, "armed": False, "phrase": self.phrase}
        low = (text or "").strip().lower()
        hit = bool(self._pattern.search(low))
        if not hit:
            # Fuzzy: "hey"/"hi" near om/jarvis in first few tokens
            toks = low.replace(",", " ").split()
            head = toks[:4]
            if any(t in {"om", "jarvis", "jarvice"} for t in head) and any(
                t in {"hey", "hi", "hello", "okay", "ok", "yo"} for t in head
            ):
                hit = True
        return {
            "detected": hit,
            "armed": self._armed,
            "phrase": self.phrase,
            "mode": "porcupine" if self._porcupine else "local_phrase",
            "matched_text": low[:120] if hit else "",
        }

    def process_pcm(self, pcm: bytes | None = None) -> dict[str, Any]:
        """Optional Porcupine frame hook for desktop always-on mic path."""
        if not self._armed or self._porcupine is None or not pcm:
            return {"detected": False, "mode": "local_phrase"}
        try:
            # Porcupine expects int16 frames; caller must pass correctly sized audio
            import struct

            frame_len = int(getattr(self._porcupine, "frame_length", 512) or 512)
            need = frame_len * 2
            if len(pcm) < need:
                return {"detected": False, "mode": "porcupine", "reason": "short_frame"}
            frame = struct.unpack_from(f"{frame_len}h", pcm, 0)
            result = self._porcupine.process(frame)
            hit = int(result) >= 0
            if hit:
                self.disarm()
            return {
                "detected": hit,
                "armed": self._armed,
                "phrase": self.phrase,
                "mode": "porcupine",
            }
        except Exception as exc:
            return {"detected": False, "mode": "porcupine", "error": str(exc)[:160]}

    def status(self) -> dict[str, Any]:
        return {
            "phrase": self.phrase,
            "armed": self._armed,
            "mode": "porcupine" if self._porcupine else "local_phrase",
            "aliases": list(self._aliases)[:12],
            "porcupine_error": self._porcupine_err,
        }
