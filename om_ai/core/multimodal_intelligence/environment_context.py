"""Environment context — project + screen + room state."""
from __future__ import annotations

from typing import Any


class EnvironmentContext:
    def __init__(self) -> None:
        self.active_project = ""
        self.last_screen = ""

    def update(
        self,
        *,
        project: str = "",
        screen: str = "",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if project:
            self.active_project = project
        if screen:
            self.last_screen = screen
        return {
            "active_project": self.active_project,
            "last_screen": self.last_screen,
            "extra": extra or {},
        }
