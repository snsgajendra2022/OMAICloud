from __future__ import annotations
from typing import Any
from .event import CompanionEvent
from .event_bus import RealtimeEventBus

class SessionChannel:
    def __init__(self, session_id: str, bus: RealtimeEventBus) -> None:
        self.session_id = session_id
        self.bus = bus
        self.clients: list[Any] = []

    def emit(self, event_type: str, payload: dict[str, Any] | None = None, *, trace_id: str = "") -> CompanionEvent:
        ev = CompanionEvent(event_type=event_type, payload=payload or {}, session_id=self.session_id, trace_id=trace_id)
        self.bus.publish(ev)
        return ev
