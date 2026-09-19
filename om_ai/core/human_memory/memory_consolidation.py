from __future__ import annotations
from typing import Any

class MemoryConsolidation:
    def summarize(self, episodes: list[dict[str, Any]]) -> str:
        if not episodes:
            return ""
        bits = [str(e.get("text") or "")[:80] for e in episodes[-5:] if e.get("text")]
        return "Recent thread: " + " | ".join(bits)
