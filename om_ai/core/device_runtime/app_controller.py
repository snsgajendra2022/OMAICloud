"""Application launch/control (macOS uses open -a with argv list)."""
from __future__ import annotations

import platform
import signal
import subprocess
from typing import Any

from om_ai.core.action_control import CommandExecutor


class AppController:
    def __init__(self, *, command_executor: CommandExecutor | None = None) -> None:
        self._cmd = command_executor or CommandExecutor()
        self._system = platform.system().lower()

    def open_application(
        self, app_name: str, args: list[str] | None = None
    ) -> dict[str, Any]:
        args = [str(a) for a in (args or [])]
        if self._system == "darwin":
            argv = ["open", "-a", app_name, *args]
        elif self._system == "linux":
            argv = [app_name, *args]
        else:
            argv = ["cmd", "/c", "start", "", app_name, *args]
        return self._cmd.run(argv)

    def close_application(self, app_name: str) -> dict[str, Any]:
        if self._system == "darwin":
            argv = ["osascript", "-e", f'tell application "{app_name}" to quit']
            return self._cmd.run(argv)
        if self._system == "linux":
            argv = ["pkill", "-x", app_name]
            return self._cmd.run(argv)
        argv = ["taskkill", "/IM", f"{app_name}.exe", "/F"]
        return self._cmd.run(argv)

    def send_signal_pid(self, pid: int, sig: int = signal.SIGTERM) -> dict[str, Any]:
        try:
            import os

            os.kill(pid, sig)
            return {"pid": pid, "signal": sig, "ok": True}
        except OSError as exc:
            return {"pid": pid, "signal": sig, "ok": False, "error": str(exc)}
