"""
Action Executor — runs permitted tools via chat_runner + specialty handlers.
"""
from __future__ import annotations

from typing import Any


class ActionExecutor:
    """Execute approved tools; never bypasses permission (caller must filter)."""

    def execute(
        self,
        tools: list[str],
        question: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = dict(context or {})
        chat_tools: list[str] = []
        specialty: list[dict[str, Any]] = []

        for name in tools:
            if name in {
                "date",
                "calculator",
                "knowledge",
                "file",
                "code_execution",
                "code",
                "web",
                "vision",
                "ocr",
            }:
                chat_tools.append("code_execution" if name == "code" else name)
            elif name == "file_manager":
                chat_tools.append("file")
            elif name == "browser":
                chat_tools.append("web")
            elif name == "database":
                specialty.append(self._run_database(question, ctx))
            elif name == "terminal":
                specialty.append(self._run_terminal(question, ctx))
            elif name == "api_client":
                specialty.append(self._run_api(question, ctx))
            else:
                specialty.append(
                    {
                        "tool": name,
                        "ok": False,
                        "output": f"unwired tool: {name}",
                        "text": "",
                    }
                )

        from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context

        out = execute_planned_tools(chat_tools, question, context=ctx) if chat_tools else {
            "enabled": True,
            "executed": [],
            "results": [],
            "texts": [],
            "combined_text": "",
            "skipped": False,
            "ok": False,
        }

        results = list(out.get("results") or [])
        texts = list(out.get("texts") or [])
        executed = list(out.get("executed") or [])

        for sp in specialty:
            results.append(sp)
            executed.append(str(sp.get("tool") or "specialty"))
            if sp.get("ok") and sp.get("text"):
                texts.append(str(sp["text"]))

        combined = "\n\n".join(t for t in texts if t)
        return {
            "enabled": True,
            "executed": executed,
            "results": results,
            "texts": texts,
            "combined_text": combined,
            "context_block": format_tool_context({"results": results, "skipped": False}),
            "ok": bool(combined),
            "skipped": False,
        }

    def _run_terminal(self, question: str, ctx: dict[str, Any]) -> dict[str, Any]:
        try:
            from om_ai.actions.shell import SafeShellTool

            cmd = str(ctx.get("command") or "").strip()
            if not cmd:
                # Extract simple allowlisted-looking command after "run"
                import re

                m = re.search(
                    r"(?:run|execute)\s+(?:command\s+)?[`'\"]?([a-zA-Z0-9_./\s\-]+)[`'\"]?",
                    question or "",
                    re.I,
                )
                cmd = (m.group(1).strip() if m else "pwd")
            result = SafeShellTool().run(command=cmd)
            text = str(result.data if result.ok else result.error or "")
            return {
                "tool": "terminal",
                "ok": bool(result.ok),
                "output": result.data if result.ok else result.error,
                "text": text[:4000],
            }
        except Exception as exc:
            return {"tool": "terminal", "ok": False, "output": str(exc), "text": ""}

    def _run_database(self, question: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """Read-only SQLite peek when path provided — no arbitrary writes."""
        import sqlite3
        from pathlib import Path

        path = str(ctx.get("db_path") or "artifacts/om_ai.sqlite3")
        p = Path(path)
        if not p.is_file():
            return {
                "tool": "database",
                "ok": False,
                "output": "db missing",
                "text": f"Database not found: {path}",
            }
        try:
            con = sqlite3.connect(f"file:{p.resolve()}?mode=ro", uri=True)
            cur = con.cursor()
            tables = [
                r[0]
                for r in cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' LIMIT 20"
                ).fetchall()
            ]
            con.close()
            text = "SQLite tables: " + ", ".join(tables) if tables else "No tables."
            return {"tool": "database", "ok": True, "output": tables, "text": text}
        except Exception as exc:
            return {"tool": "database", "ok": False, "output": str(exc), "text": ""}

    def _run_api(self, question: str, ctx: dict[str, Any]) -> dict[str, Any]:
        """SSRF-safe GET when URL explicitly in context."""
        import os

        url = str(ctx.get("url") or "").strip()
        if not url.startswith("https://"):
            return {
                "tool": "api_client",
                "ok": False,
                "output": "https url required in context",
                "text": "",
            }
        if os.environ.get("OM_LIVE_KNOWLEDGE_NETWORK", "0") != "1":
            return {
                "tool": "api_client",
                "ok": False,
                "output": "OM_LIVE_KNOWLEDGE_NETWORK=0",
                "text": "",
            }
        try:
            import httpx

            r = httpx.get(url, timeout=8.0, follow_redirects=False)
            body = r.text[:2000]
            return {
                "tool": "api_client",
                "ok": r.status_code < 400,
                "output": {"status": r.status_code},
                "text": f"HTTP {r.status_code}\n{body}",
            }
        except Exception as exc:
            return {"tool": "api_client", "ok": False, "output": str(exc), "text": ""}
