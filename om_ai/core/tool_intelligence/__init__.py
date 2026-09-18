"""STEP 31 — OM Tool Intelligence (ChatGPT tools style)."""
from __future__ import annotations

from typing import Any


class ToolIntelligence:
    TOOLS = ("browser", "files", "code_execution", "database", "apis", "automation")

    def route(self, message: str) -> dict[str, Any]:
        low = (message or "").lower()
        wanted = []
        mapping = {
            "browser": ("search", "web", "browse", "latest", "url"),
            "files": ("file", "read", "write", "upload", "document"),
            "code_execution": ("run code", "execute", "python eval", "repl"),
            "database": ("sql", "database", "query table"),
            "apis": ("api", "http", "endpoint", "webhook"),
            "automation": ("automate", "schedule", "workflow", "script"),
        }
        for tool, words in mapping.items():
            if any(w in low for w in words):
                wanted.append(tool)
        return {
            "step": 31,
            "tools": wanted or ["none"],
            "available": list(self.TOOLS),
            "needs_tools": bool(wanted),
            "plan": [f"use:{t}" for t in wanted],
        }

    def run(self, message: str) -> dict[str, Any]:
        route = self.route(message)
        return {
            **route,
            "answer": (
                "I can use tools for this: " + ", ".join(route["tools"])
                if route["needs_tools"]
                else "No external tool required for this message."
            ),
        }


def run_tool_intelligence(message: str) -> dict[str, Any]:
    return ToolIntelligence().run(message)


__all__ = ["ToolIntelligence", "run_tool_intelligence"]
