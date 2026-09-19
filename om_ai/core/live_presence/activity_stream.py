from __future__ import annotations
from typing import Any
from .event_bus import get_event_bus

class ActivityStream:
    def push(self, label: str) -> dict[str, Any]:
        return get_event_bus().emit("activity", {"label": label})

    def list(self, n: int = 12) -> list[str]:
        out = []
        for ev in get_event_bus().recent(n * 2):
            if ev.get("event_type") == "activity":
                lab = (ev.get("payload") or {}).get("label")
                if lab:
                    out.append(str(lab))
        return out[-n:]
