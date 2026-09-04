"""
OM Tool Router — select AND execute the best tool.
"""
from __future__ import annotations

from typing import Any

from .file_tool import FileTool
from .code_tool import CodeTool
from .data_tool import DataTool


class ToolRouter:
    def __init__(self) -> None:
        self.tools = [FileTool(), CodeTool(), DataTool()]

    def route(self, request: str) -> dict[str, Any]:
        results = []
        for tool in self.tools:
            score = tool.can_handle(request)
            results.append({"tool": tool, "name": tool.name, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        best = results[0]
        return {
            "name": best["name"],
            "score": best["score"],
            "tool": best["tool"],
        }

    def execute(self, request: str, context: dict | None = None) -> dict[str, Any]:
        """Route then run — chat/cognitive paths must call this, not only route()."""
        picked = self.route(request)
        tool = picked.get("tool")
        if tool is None or float(picked.get("score") or 0) <= 0:
            # Fall through to chat runner knowledge
            try:
                from om_ai.tools.chat_runner import execute_planned_tools

                return execute_planned_tools(["knowledge"], request, context=context or {})
            except Exception as exc:
                return {"ok": False, "error": str(exc), "tool": None}
        try:
            out = tool.execute(request, context)
            return {"ok": True, "selected": picked["name"], "score": picked["score"], "result": out}
        except Exception as exc:
            return {"ok": False, "selected": picked["name"], "error": str(exc)}
