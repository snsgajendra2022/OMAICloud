"""Segment continuous audio into utterance windows."""
from __future__ import annotations

from typing import Any


class SpeechSegmenter:
    def __init__(self) -> None:
        self._buf: list[str] = []

    def push_partial(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        if t:
            self._buf.append(t)
        joined = " ".join(self._buf).strip()
        return {"segment": joined, "chunks": len(self._buf), "open": True}

    def commit(self, final: str = "") -> dict[str, Any]:
        t = (final or "").strip() or " ".join(self._buf).strip()
        self._buf.clear()
        return {"segment": t, "open": False, "committed": bool(t)}

    def reset(self) -> None:
        self._buf.clear()
