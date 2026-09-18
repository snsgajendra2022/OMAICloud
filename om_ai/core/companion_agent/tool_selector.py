"""Map natural-language task hints to device capabilities."""
from __future__ import annotations

from .task import Task


class ToolSelector:
    _KEYWORDS: dict[str, str] = {
        "open app": "application.open",
        "launch": "application.open",
        "read file": "filesystem.read",
        "write file": "filesystem.write",
        "list dir": "filesystem.list",
        "browse": "browser.open",
        "navigate": "browser.navigate",
        "notify": "system.notification",
        "process list": "process.list",
    }

    def select_capability(self, task: Task) -> str | None:
        if task.capability:
            return task.capability
        lower = task.description.lower()
        for phrase, cap in self._KEYWORDS.items():
            if phrase in lower:
                return cap
        return None
