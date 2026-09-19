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

    def set_volume(self, level: int | None = None, *, mute: bool | None = None) -> dict[str, Any]:
        """0–100 output volume, or mute/unmute (macOS / Linux best-effort)."""
        if self._system == "darwin":
            if mute is True:
                return self._cmd.run(["osascript", "-e", "set volume output muted true"])
            if mute is False:
                return self._cmd.run(["osascript", "-e", "set volume output muted false"])
            lvl = max(0, min(100, int(level if level is not None else 50)))
            return self._cmd.run(["osascript", "-e", f"set volume output volume {lvl}"])
        if self._system == "linux" and level is not None:
            lvl = max(0, min(100, int(level)))
            return self._cmd.run(["amixer", "-D", "pulse", "sset", "Master", f"{lvl}%"])
        return {"ok": False, "reason": "volume_unsupported"}

