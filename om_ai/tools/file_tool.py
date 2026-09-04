"""File Management Tool — safe read/list in workspace."""
from __future__ import annotations

from pathlib import Path

from .base import BaseTool


class FileTool(BaseTool):
    name = "file"

    def can_handle(self, request: str) -> float:
        keywords = ["file", "folder", "read", "write", "create", "open", "readme", "list"]
        score = 0.0
        for word in keywords:
            if word in (request or "").lower():
                score += 0.15
        return min(score, 1.0)

    def execute(self, request, context=None):
        try:
            from om_ai.tools.chat_runner import _run_file

            root = "."
            if isinstance(context, dict):
                root = str(context.get("project_root") or context.get("root") or ".")
            return _run_file(request or "", root=root)
        except Exception as exc:
            return {
                "tool": self.name,
                "ok": False,
                "action": "file_operation",
                "status": "error",
                "error": str(exc),
            }
