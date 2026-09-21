"""Capability registry — everything is a capability."""
from __future__ import annotations

from typing import Any, Callable

from .capability_health import CapabilityHealth
from .capability_loader import CapabilityLoader
from .tool_executor import ToolExecutor
from .tool_monitor import ToolMonitor
from .tool_permission import ToolPermission
from .tool_schema import ToolSchema

_SYS: "CapabilityRegistry | None" = None


class CapabilityRegistry:
    def __init__(self) -> None:
        self.loader = CapabilityLoader()
        self.permission = ToolPermission()
        self.executor = ToolExecutor()
        self.monitor = ToolMonitor()
        self.health = CapabilityHealth()
        self.tools: dict[str, ToolSchema] = {t.id: t for t in self.loader.load()}
        # Bridge older capability measurement layer if present
        try:
            from om_ai.core.capability import CapabilityRegistry as LegacyReg

            self._legacy = LegacyReg()
        except Exception:
            self._legacy = None

    def list(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.tools.values()]

    def register_handler(self, tool_id: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self.executor.register(tool_id, handler)

    def invoke(
        self,
        tool_id: str,
        params: dict[str, Any] | None = None,
        *,
        allowed: set[str] | None = None,
    ) -> dict[str, Any]:
        tool = self.tools.get(tool_id)
        if not tool:
            return {"ok": False, "error": f"Unknown capability: {tool_id}"}
        gate = self.permission.check(tool, allowed=allowed)
        if not gate.get("allowed"):
            return {"ok": False, "permission": gate, "tool": tool_id}
        result = self.executor.execute(tool, params)
        self.monitor.record(tool_id, result)
        return result

    def status(self) -> dict[str, Any]:
        handlers = set(self.executor._handlers.keys())
        return {
            "step": 67,
            "tools": len(self.tools),
            "health": self.health.check(list(self.tools.values()), handlers=handlers),
            "recent": self.monitor.recent(5),
        }


def get_capability_system() -> CapabilityRegistry:
    global _SYS
    if _SYS is None:
        _SYS = CapabilityRegistry()
    return _SYS
