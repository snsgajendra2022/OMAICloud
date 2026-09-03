"""Load conversation / project / preference context before answering."""
from __future__ import annotations

from typing import Any


class ContextManager:
    def load(
        self,
        question: str,
        *,
        messages: list[dict] | None = None,
        memory_context: dict | list | None = None,
        user_profile: dict | None = None,
        project: dict | str | None = None,
    ) -> dict[str, Any]:
        history = []
        for m in (messages or [])[-10:]:
            role = str(m.get("role") or "")
            content = str(m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                history.append({"role": role, "content": content[:400]})

        project_hint = ""
        if isinstance(project, dict):
            project_hint = str(project.get("name") or project.get("id") or "")
        elif project:
            project_hint = str(project)

        prefs = user_profile or {}
        mem_items: list[str] = []
        if isinstance(memory_context, dict):
            rel = memory_context.get("relevant") or []
            if isinstance(rel, list):
                mem_items = [str(x)[:300] for x in rel[:8]]
        elif isinstance(memory_context, list):
            mem_items = [str(x)[:300] for x in memory_context[:8]]

        prior_user = [h["content"] for h in history if h["role"] == "user"]
        return {
            "question": question,
            "history": history,
            "prior_user": prior_user[-5:],
            "project_hint": project_hint,
            "preferences": prefs.get("preferences") if isinstance(prefs, dict) else {},
            "technologies": (prefs.get("technologies") if isinstance(prefs, dict) else []) or [],
            "memory_items": mem_items,
        }
