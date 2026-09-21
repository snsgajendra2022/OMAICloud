"""Monitor tool calls."""
from __future__ import annotations

import time
from typing import Any


class ToolMonitor:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, tool_id: str, result: dict[str, Any]) -> None:
        self.events.append(
            {
                "ts": time.time(),
                "tool": tool_id,
                "ok": bool(result.get("ok")),
                "message": str(result.get("message") or result.get("error") or "")[:200],
            }
        )
        self.events = self.events[-100:]

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        return list(self.events[-n:])
