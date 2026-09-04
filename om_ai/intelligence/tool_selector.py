"""Decide which tools are needed — capability inference, not manual maps."""
from __future__ import annotations

import re
from typing import Any


class ToolSelector:
    def select(
        self,
        understanding: dict[str, Any],
        intent: dict[str, Any],
        *,
        knowledge: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        domain = str(understanding.get("domain") or "")
        action = str(understanding.get("required_action") or "")
        intent_name = str(intent.get("intent") or "")
        q = str(understanding.get("raw") or "").lower()

        tools: list[str] = []
        reasons: dict[str, str] = {}

        def need(name: str, why: str) -> None:
            if name not in tools:
                tools.append(name)
                reasons[name] = why

        if domain == "time" or intent_name in {"datetime", "date_request"}:
            # Never treat social "how was your date/day" as calendar
            if not re.search(
                r"\bhow\s+(was|is|are)\s+(your\s+)?(day|date)\b",
                q,
            ) and re.search(
                r"\b(today'?s?\s+date|current\s+date|what(?:'s|\s+is)\s+(?:the\s+)?date|"
                r"current\s+time|what(?:'s|\s+is)\s+the\s+time|what\s+day\s+is\s+it)\b",
                q,
            ):
                need("date", "temporal question")
        if action == "calculate" or any(x in q for x in ("calculate", "compute", "%", "sum")):
            need("calculator", "numeric computation")
        if action in {"research", "recommend"} or "latest" in q or "news" in q:
            need("web", "external or fresh info may help")
        if domain in {"software", "data", "architecture"} and action in {"generate", "debug", "create"}:
            need("code_execution", "validate or illustrate code")
        if "database" in q or "sql" in q or domain == "data":
            need("database", "data/schema work")
        if "file" in q or "readme" in q or action == "generate" and domain == "software":
            need("file", "file-oriented deliverable")

        # Knowledge packets already satisfy date — still list the tool
        if knowledge and any(p.get("source") == "calendar_clock" for p in knowledge.get("packets") or []):
            need("date", "clock knowledge attached")

        return {
            "tools": tools,
            "reasons": reasons,
            "needed": bool(tools),
        }
