"""Rolling wellbeing context across turns."""
from __future__ import annotations

from typing import Any


class WellbeingContext:
    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def push(self, pack: dict[str, Any]) -> None:
        if pack.get("has_signal"):
            self._events.append(pack)
            self._events = self._events[-20:]

    def summary(self) -> dict[str, Any]:
        if not self._events:
            return {"recent_signals": [], "dominant": None}
        sigs = [str(e.get("signal") or "") for e in self._events[-5:]]
        dominant = max(set(sigs), key=sigs.count) if sigs else None
        return {
            "recent_signals": sigs,
            "dominant": dominant,
            "count": len(self._events),
        }
