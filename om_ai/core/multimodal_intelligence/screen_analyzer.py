"""Screen analyzer — 'what is wrong here?' on a capture."""
from __future__ import annotations

from typing import Any


class ScreenAnalyzer:
    def analyze(self, screen_ref: str | None = None, *, user_question: str = "") -> dict[str, Any]:
        q = (user_question or "").lower()
        focus = "ui"
        if any(w in q for w in ("error", "bug", "wrong", "fail", "exception")):
            focus = "error"
        elif any(w in q for w in ("code", "function", "file")):
            focus = "code"
        return {
            "has_screen": bool(screen_ref),
            "focus": focus,
            "screen_ref": screen_ref or "",
            "hint": (
                "Inspect the visible error / UI state and relate it to the active project."
                if focus == "error"
                else "Describe what is on screen in context of the current task."
            ),
            "system_hint": (
                "User shared screen context. Combine vision summary with project memory. "
                "Explain the issue clearly; do not invent file contents you cannot see."
            ),
        }
