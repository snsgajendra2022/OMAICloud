from __future__ import annotations
from typing import Iterator

class StreamingVoice:
    def chunks(self, text: str, size: int = 80) -> Iterator[str]:
        t = text or ""
        for i in range(0, len(t), size):
            yield t[i : i + size]
