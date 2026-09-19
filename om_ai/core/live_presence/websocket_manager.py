from __future__ import annotations
from typing import Any

class WebSocketManager:
    """Thin adapter — companion routes already own the live WebSocket hub."""

    def __init__(self) -> None:
        self.sessions: dict[str, Any] = {}

    def register(self, session_id: str, ws: Any) -> None:
        self.sessions[session_id] = ws

    def unregister(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def status(self) -> dict[str, Any]:
        return {"sessions": len(self.sessions), "step": 110}
