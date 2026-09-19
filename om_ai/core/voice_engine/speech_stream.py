"""Streaming speech chunk helper."""
from __future__ import annotations

import re
from typing import Iterator


class SpeechStream:
    def chunks(self, text: str, *, max_chars: int = 160) -> Iterator[str]:
        t = (text or "").strip()
        if not t:
            return
        parts = re.split(r"(?<=[.!?।])\s+", t)
        buf = ""
        for p in parts:
            if not p:
                continue
            if len(buf) + len(p) + 1 <= max_chars:
                buf = f"{buf} {p}".strip()
            else:
                if buf:
                    yield buf
                buf = p
        if buf:
            yield buf
