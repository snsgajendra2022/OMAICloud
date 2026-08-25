"""Tool registry facade over om_ai.actions (+ future integrations)."""
from __future__ import annotations

from typing import Any, Callable


TOOL_CATALOG = {
    "file_manager": "Read/write/list files (workspace scoped)",
    "terminal": "Allowlisted shell commands",
    "browser": "Gated web fetch / browse",
    "database": "SQL / RAG store access",
    "api_client": "HTTP API calls with SSRF guards",
    "git": "Status / diff / commit helpers",
    "cloud": "Cloud automation stubs",
    "automation": "Workflow automation stubs",
}


def list_tools() -> dict[str, str]:
    return dict(TOOL_CATALOG)


def select_tool(goal: str) -> str:
    g = (goal or "").lower()
    if any(w in g for w in ("git", "commit", "branch", "diff")):
        return "git"
    if any(w in g for w in ("shell", "terminal", "bash", "run command")):
        return "terminal"
    if any(w in g for w in ("http", "api", "request", "curl")):
        return "api_client"
    if any(w in g for w in ("sql", "database", "postgres", "sqlite")):
        return "database"
    if any(w in g for w in ("browser", "web", "url", "scrape")):
        return "browser"
    if any(w in g for w in ("file", "read", "write", "path")):
        return "file_manager"
    return "file_manager"


def execute_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a registered tool safely; prefer existing action implementations."""
    name = name or select_tool(str(kwargs.get("goal") or ""))
    if name == "terminal":
        from om_ai.actions.shell import SafeShellTool

        cmd = str(kwargs.get("command") or "pwd")
        result = SafeShellTool().run(command=cmd)
        return {
            "tool": name,
            "ok": bool(result.ok),
            "output": result.data if result.ok else result.error,
        }
    if name in {"database", "file_manager"}:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        q = str(kwargs.get("query") or kwargs.get("goal") or "")
        hits = VectorKnowledgeLayer().search(q, k=3) if q else []
        return {
            "tool": name,
            "ok": True,
            "output": hits,
        }
    return {
        "tool": name,
        "ok": False,
        "output": f"Tool '{name}' is registered but needs explicit wiring/credentials.",
        "catalog": TOOL_CATALOG.get(name, ""),
    }


def run_tool_loop(goal: str) -> dict[str, Any]:
    """Brain → select → execute → analyze."""
    tool = select_tool(goal)
    result = execute_tool(tool, goal=goal, query=goal, command="pwd")
    return {
        "goal": goal,
        "selected": tool,
        "result": result,
        "analysis": "Inspect output; retry with another tool if insufficient.",
    }
