"""System-level notifications and lightweight controls."""
from __future__ import annotations

import platform
from typing import Any

from om_ai.core.action_control import CommandExecutor


class SystemController:
    def __init__(self, *, command_executor: CommandExecutor | None = None) -> None:
        self._cmd = command_executor or CommandExecutor()
        self._system = platform.system().lower()

    def notification(self, title: str, message: str) -> dict[str, Any]:
        title = title[:256]
        message = message[:2048]
        if self._system == "darwin":
            script = (
                f'display notification "{message}" with title "{title}"'
            )
            return self._cmd.run(["osascript", "-e", script])
        if self._system == "linux":
            return self._cmd.run(["notify-send", title, message])
        return {
            "title": title,
            "message": message,
            "delivered": False,
            "reason": "notifications not configured for this platform",
        }
