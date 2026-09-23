"""Action planner adapter for architecture layer 8."""
from __future__ import annotations

from typing import Any


class ActionPlanner:
    def plan(self, message: str) -> dict[str, Any] | None:
        try:
            from om_ai.core.companion_architecture.companion_pipeline import CompanionPipeline

            return CompanionPipeline()._detect_action(message, loc="en")
        except Exception:
            return None
