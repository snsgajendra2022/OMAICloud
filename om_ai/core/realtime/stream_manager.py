from __future__ import annotations
from typing import Any
from .event_bus import RealtimeEventBus
from .session_channel import SessionChannel
from .websocket_hub import WebSocketHub

class StreamManager:
    def __init__(self) -> None:
        self.bus = RealtimeEventBus()
        self.hub = WebSocketHub(self.bus)
        self._channels: dict[str, SessionChannel] = {}

    def channel(self, session_id: str) -> SessionChannel:
        if session_id not in self._channels:
            self._channels[session_id] = SessionChannel(session_id, self.bus)
        return self._channels[session_id]

    def status(self) -> dict[str, Any]:
        return {"channels": list(self._channels), "recent": len(self.bus.recent())}
