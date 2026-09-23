"""Action planning route — returns a spoken/plan string for the user."""
from __future__ import annotations

from typing import Any


class ActionEngine:
    """Chat-facing action planner with an `.execute()` string API."""

    def execute(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> str:
        _ = context
        q = (message or "").strip()
        if not q:
            return "What would you like me to do?"

        try:
            from om_ai.core.action_engine import ActionEngine as CoreActionEngine

            plan = CoreActionEngine().plan(q, execute=False)
            spoken = str(plan.get("spoken") or "").strip()
            if spoken:
                return spoken
            steps = plan.get("steps") or []
            if steps:
                lines = ["Here's the plan:", ""]
                for i, step in enumerate(steps, 1):
                    label = step.get("label") if isinstance(step, dict) else str(step)
                    lines.append(f"{i}. {label}")
                return "\n".join(lines)
        except Exception:
            pass

        return (
            f"I can help with that. I'll break “{q}” into clear steps "
            "and proceed carefully — tell me if you want me to start."
        )
