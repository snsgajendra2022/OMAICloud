"""Tool registry facade over om_ai.actions (+ chat tool runner + action layer)."""
from __future__ import annotations

from typing import Any

from .router import ToolRouter
from .chat_runner import execute_planned_tools, format_tool_context, tools_enabled

__all__ = [
    "ToolRouter",
    "TOOL_CATALOG",
    "list_tools",
    "select_tool",
    "execute_tool",
    "run_tool_loop",
    "execute_planned_tools",
    "format_tool_context",
    "tools_enabled",
    "run_action_layer",
]

TOOL_CATALOG = {
    "file_manager": "Read/write/list files (workspace scoped)",
    "terminal": "Allowlisted shell commands",
    "browser": "Gated web fetch / browse",
    "database": "SQL / RAG store access",
    "api_client": "HTTP API calls with SSRF guards",
    "git": "Status / diff / commit helpers",
    "cloud": "Cloud automation stubs",
    "automation": "Workflow automation stubs",
    "knowledge": "Dataset brain + RAG retrieval",
    "code_execution": "Coding brain / analysis",
    "date": "Current date/time",
    "calculator": "Arithmetic / percent",
    "web": "Internet intelligence (permissioned)",
    "vision": "Image / OCR analysis",
}


def list_tools() -> dict[str, str]:
    return dict(TOOL_CATALOG)


def select_tool(goal: str) -> str:
    try:
        from om_ai.tools.intelligence import ToolDecisionEngine

        d = ToolDecisionEngine().decide(goal)
        if d.tools:
            return d.tools[0]
    except Exception:
        pass
    g = (goal or "").lower()
    if any(w in g for w in ("git", "commit", "branch", "diff")):
        return "git"
    if any(w in g for w in ("shell", "terminal", "bash", "run command")):
        return "terminal"
    if any(w in g for w in ("http", "api", "request", "curl")):
        return "api_client"
    if any(w in g for w in ("sql", "database", "postgres", "sqlite")):
        return "database"
    if any(w in g for w in ("browser", "web", "url", "scrape", "weather")):
        return "web"
    if any(w in g for w in ("code", "python", "function", "debug", "bug")):
        return "code_execution"
    if any(w in g for w in ("file", "read", "write", "path", "readme")):
        return "file_manager"
    return "knowledge"


def execute_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a registered tool safely."""
    name = name or select_tool(str(kwargs.get("goal") or ""))
    mapped = {
        "file_manager": "file",
        "database": "database",
        "browser": "web",
    }.get(name, name)
    if mapped in {
        "date",
        "calculator",
        "knowledge",
        "file",
        "code_execution",
        "code",
        "web",
        "vision",
        "ocr",
        "terminal",
        "database",
        "api_client",
    }:
        try:
            from om_ai.tools.intelligence import AutonomousActionLayer

            action = AutonomousActionLayer().run(
                str(kwargs.get("query") or kwargs.get("goal") or ""),
                context=kwargs.get("context") or {},
                capability={"capability": mapped},
            )
            results = (action.execution or {}).get("results") or []
            if results:
                return results[0]
            if not action.needs_tools:
                return {
                    "tool": mapped,
                    "ok": False,
                    "output": "no_tools_needed",
                    "text": "",
                    "mode": action.mode,
                }
        except Exception:
            pass
        out = execute_planned_tools(
            [mapped if mapped != "database" else "knowledge"],
            str(kwargs.get("query") or kwargs.get("goal") or ""),
            context=kwargs.get("context") or {},
        )
        results = out.get("results") or []
        return results[0] if results else {"tool": name, "ok": False, "output": ""}

    if name == "terminal":
        from om_ai.actions.shell import SafeShellTool

        cmd = str(kwargs.get("command") or "pwd")
        result = SafeShellTool().run(command=cmd)
        return {
            "tool": name,
            "ok": bool(result.ok),
            "output": result.data if result.ok else result.error,
        }
    return {
        "tool": name,
        "ok": False,
        "output": f"Tool '{name}' is registered but needs explicit wiring/credentials.",
        "catalog": TOOL_CATALOG.get(name, ""),
    }


def run_tool_loop(goal: str) -> dict[str, Any]:
    """Brain → select → execute → analyze (STEP 86)."""
    return run_action_layer(goal)


def run_action_layer(goal: str, **kwargs: Any) -> dict[str, Any]:
    from om_ai.tools.intelligence import AutonomousActionLayer

    result = AutonomousActionLayer(
        identity=str((kwargs.get("context") or {}).get("actor") or "default")
    ).run(
        goal,
        context=kwargs.get("context"),
        intent=kwargs.get("intent"),
        capability=kwargs.get("capability"),
        understanding=kwargs.get("understanding"),
    )
    return result.to_dict()
