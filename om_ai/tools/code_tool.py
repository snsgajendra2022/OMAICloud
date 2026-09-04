"""Code Analysis Tool — real coding_brain call, not a stub."""
from __future__ import annotations

from .base import BaseTool


class CodeTool(BaseTool):
    name = "code"

    def can_handle(self, request) -> float:
        keywords = ["debug", "error", "bug", "code", "function", "class", "python", "react"]
        return 0.8 if any(x in (request or "").lower() for x in keywords) else 0.0

    def execute(self, request, context=None):
        try:
            from om_ai.tools.chat_runner import _run_code

            root = "."
            if isinstance(context, dict):
                root = str(context.get("project_root") or context.get("root") or ".")
            return _run_code(request or "", root=root)
        except Exception as exc:
            return {"tool": "code", "ok": False, "operation": "analysis", "error": str(exc)}
