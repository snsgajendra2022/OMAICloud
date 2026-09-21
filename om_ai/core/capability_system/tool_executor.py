"""Tool executor — dispatches to DeviceRuntime / ActionControl when available."""
from __future__ import annotations

from typing import Any, Callable

from .tool_schema import ToolSchema


class ToolExecutor:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, tool_id: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._handlers[tool_id] = handler

    def execute(self, tool: ToolSchema, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        handler = self._handlers.get(tool.id)
        if not handler:
            return {
                "ok": False,
                "tool": tool.id,
                "message": f"Capability '{tool.id}' registered but no live handler yet.",
            }
        try:
            out = handler(params)
            return {"ok": bool(out.get("ok", True)), "tool": tool.id, **(out if isinstance(out, dict) else {"result": out})}
        except Exception as exc:
            return {"ok": False, "tool": tool.id, "error": str(exc)}
