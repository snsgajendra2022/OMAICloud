"""Action subsystem facade — planner + permission + verify."""
from __future__ import annotations

from typing import Any, Callable


class ActionSubsystem:
    def __init__(
        self,
        *,
        plan_fn: Callable[[str, dict[str, Any]], dict[str, Any] | None] | None = None,
        execute_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        looks_fn: Callable[[str], bool] | None = None,
    ) -> None:
        self._plan = plan_fn
        self._execute = execute_fn
        self._looks = looks_fn

    def looks_like_action(self, text: str) -> bool:
        if self._looks:
            return bool(self._looks(text))
        return False

    def plan(self, text: str, semantic: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if self._plan:
            return self._plan(text, semantic or {})
        return None

    def execute(self, planned: dict[str, Any]) -> dict[str, Any]:
        if self._execute:
            return self._execute(planned)
        return {"ok": False, "message": "No executor"}
