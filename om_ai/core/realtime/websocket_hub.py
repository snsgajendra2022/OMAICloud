from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
from .event import CompanionEvent
from .event_bus import RealtimeEventBus

logger = logging.getLogger(__name__)

class WebSocketHub:
    def __init__(self, bus: RealtimeEventBus | None = None) -> None:
        self.bus = bus or RealtimeEventBus()
        self._sockets: dict[str, list[Any]] = {}
        self.bus.subscribe_all(self._fanout)

    def register(self, session_id: str, websocket: Any) -> None:
        self._sockets.setdefault(session_id, []).append(websocket)

    def unregister(self, session_id: str, websocket: Any) -> None:
        socks = self._sockets.get(session_id) or []
        self._sockets[session_id] = [s for s in socks if s is not websocket]

    def _fanout(self, event: CompanionEvent) -> None:
        data = event.to_dict()
        for sid, socks in list(self._sockets.items()):
            if event.session_id and sid != event.session_id:
                continue
            for ws in list(socks):
                try:
                    # sync-compatible best effort
                    send = getattr(ws, "send_json", None) or getattr(ws, "send_text", None)
                    if send is None:
                        continue
                    result = send(data if hasattr(ws, "send_json") else json.dumps(data))
                    if asyncio.iscoroutine(result):
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(result)
                            else:
                                loop.run_until_complete(result)
                        except Exception:
                            pass
                except Exception as exc:
                    logger.debug("ws fanout failed: %s", exc)
