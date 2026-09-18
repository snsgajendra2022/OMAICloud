from __future__ import annotations
from collections import defaultdict
from typing import Any, Callable
from .event import CompanionEvent

class RealtimeEventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable[[CompanionEvent], None]]] = defaultdict(list)
        self._all: list[Callable[[CompanionEvent], None]] = []
        self._history: list[CompanionEvent] = []

    def subscribe(self, event_type: str, handler: Callable[[CompanionEvent], None]) -> None:
        self._subs[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[CompanionEvent], None]) -> None:
        self._all.append(handler)

    def publish(self, event: CompanionEvent) -> None:
        self._history.append(event)
        if len(self._history) > 2000:
            self._history = self._history[-2000:]
        for h in list(self._all):
            try: h(event)
            except Exception: pass
        for h in list(self._subs.get(event.event_type) or []):
            try: h(event)
            except Exception: pass

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._history[-limit:]]
