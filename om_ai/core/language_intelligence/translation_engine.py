from __future__ import annotations
from typing import Any

class TranslationEngine:
    """Optional bridge — keep original; normalize slots without full MT."""

    def normalize_for_planner(self, text: str, parsed: dict[str, Any]) -> str:
        intent = parsed.get("intent")
        slots = parsed.get("slots") or {}
        if intent == "create_reminder":
            return f"Remind me {slots.get('when', '')}: {slots.get('task', text)}"
        if intent == "continue_work":
            return "Continue my OM project work from where we left off"
        if intent == "open_editor":
            return "Open Visual Studio Code for my project"
        return text
