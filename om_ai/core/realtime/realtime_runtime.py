from __future__ import annotations
from typing import Any
from .stream_manager import StreamManager

class RealtimeRuntime:
    def __init__(self) -> None:
        self.streams = StreamManager()

    def emit(self, session_id: str, event_type: str, payload: dict[str, Any] | None = None, *, trace_id: str = "") -> dict[str, Any]:
        ev = self.streams.channel(session_id).emit(event_type, payload, trace_id=trace_id)
        return ev.to_dict()

    def status(self) -> dict[str, Any]:
        return {"ok": True, **self.streams.status()}
