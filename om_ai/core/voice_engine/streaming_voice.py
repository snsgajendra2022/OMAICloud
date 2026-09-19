"""STEP 3 — Realtime speaking chunks with emotion metadata."""
from __future__ import annotations

import re
from typing import Any, Iterator


class StreamingVoice:
    def chunks(self, text: str, *, max_chars: int = 160, size: int | None = None) -> Iterator[str]:
        limit = size or max_chars
        t = (text or "").strip()
        if not t:
            return
        parts = re.split(r"(?<=[.!?।])\s+", t)
        buf = ""
        for p in parts:
            if not p:
                continue
            if len(buf) + len(p) + 1 <= limit:
                buf = f"{buf} {p}".strip()
            else:
                if buf:
                    yield buf
                if len(p) > limit:
                    for i in range(0, len(p), limit):
                        yield p[i : i + limit]
                    buf = ""
                else:
                    buf = p
        if buf:
            yield buf

    def stream_turns(
        self,
        text: str,
        *,
        emotion: str = "calm",
        max_chars: int = 160,
    ) -> Iterator[dict[str, Any]]:
        """Yield progressive speak units for realtime playback + lip sync."""
        parts = list(self.chunks(text, max_chars=max_chars))
        if not parts:
            yield {"index": 0, "text": "", "emotion": emotion, "final": True}
            return
        last = len(parts) - 1
        for idx, chunk in enumerate(parts):
            yield {
                "index": idx,
                "text": chunk,
                "emotion": emotion,
                "final": idx == last,
            }

# Back-compat alias
SpeechStream = StreamingVoice
