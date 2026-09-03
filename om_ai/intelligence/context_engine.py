"""Conversation / project context before answering."""
from __future__ import annotations

from typing import Any


class ContextEngine:
    """Build a working context pack from messages + memory + preferences."""

    def build(
        self,
        question: str,
        *,
        messages: list[dict] | None = None,
        memory: dict | list | None = None,
        user_profile: dict | None = None,
        project: dict | str | None = None,
    ) -> dict[str, Any]:
        history = []
        for m in (messages or [])[-12:]:
            role = str(m.get("role") or "")
            content = str(m.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                history.append({"role": role, "content": content[:500]})

        recent_tasks = [
            h["content"]
            for h in history
            if h["role"] == "user"
        ][-5:]

        project_hint = ""
        if isinstance(project, dict):
            project_hint = str(project.get("name") or project.get("title") or project.get("id") or "")
        elif project:
            project_hint = str(project)

        # Soft inference: if prior turns mention a product, carry it forward
        blob = " ".join(recent_tasks).lower()
        if not project_hint:
            for hint in ("om ai", "react", "laravel", "fastapi", "cursor"):
                if hint in blob:
                    project_hint = hint
                    break

        prefs = {}
        if isinstance(user_profile, dict):
            prefs = {
                "technologies": user_profile.get("technologies") or [],
                "skills": user_profile.get("skills") or [],
                "preferences": user_profile.get("preferences") or {},
            }

        return {
            "question": question,
            "history": history,
            "recent_tasks": recent_tasks,
            "project_hint": project_hint,
            "project": project_hint,
            "user_profile": prefs,
            "memory_snapshot": memory if isinstance(memory, (dict, list)) else {},
            "interpretation": self._interpret(question, project_hint, recent_tasks),
        }

    def _interpret(self, question: str, project_hint: str, recent: list[str]) -> str:
        q = (question or "").lower()
        if "prompt" in q and project_hint:
            return f"Likely wants a development prompt related to {project_hint}."
        if recent and len(q.split()) <= 4:
            return f"Short follow-up; prior focus: {recent[-1][:80]}"
        return "Standalone request."
