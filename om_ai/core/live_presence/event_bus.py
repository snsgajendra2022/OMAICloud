from __future__ import annotations
from collections import deque
from typing import Any, Callable

_BUS = None

class EventBus:
    def __init__(self, maxlen: int = 200) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._subs: list[Callable[[dict[str, Any]], None]] = []

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        ev = {"event_type": event_type, "payload": payload or {}}
        self._events.append(ev)
        for fn in list(self._subs):
            try:
                fn(ev)
            except Exception:
                pass
        return ev

    def subscribe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        self._subs.append(fn)

    def recent(self, n: int = 20) -> list[dict[str, Any]]:
        return list(self._events)[-n:]

def get_event_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
