"""Capability health checks."""
from __future__ import annotations

from typing import Any

from .tool_schema import ToolSchema


class CapabilityHealth:
    def check(self, tools: list[ToolSchema], *, handlers: set[str]) -> dict[str, Any]:
        ready = [t.id for t in tools if t.id in handlers]
        pending = [t.id for t in tools if t.id not in handlers]
        return {
            "total": len(tools),
            "ready": len(ready),
            "pending": pending,
            "health": "ok" if ready else "degraded",
        }
