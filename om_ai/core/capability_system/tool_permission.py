"""Permission gate for tools."""
from __future__ import annotations

from typing import Any

from .tool_schema import ToolSchema


class ToolPermission:
    def check(self, tool: ToolSchema, *, allowed: set[str] | None = None) -> dict[str, Any]:
        allowed = allowed or set()
        if not tool.requires_permission:
            return {"allowed": True, "needs_prompt": False}
        if tool.id in allowed or tool.category in allowed:
            return {"allowed": True, "needs_prompt": False}
        return {
            "allowed": False,
            "needs_prompt": True,
            "prompt": f"Allow OM to use {tool.name}?",
        }
