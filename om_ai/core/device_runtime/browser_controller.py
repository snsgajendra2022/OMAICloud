"""Browser open/navigate via OS handlers."""
from __future__ import annotations

import platform
from typing import Any

from om_ai.core.action_control import CommandExecutor


class BrowserController:
    def __init__(self, *, command_executor: CommandExecutor | None = None) -> None:
        self._cmd = command_executor or CommandExecutor()
        self._system = platform.system().lower()

    def open_url(self, url: str) -> dict[str, Any]:
        if self._system == "darwin":
            return self._cmd.run(["open", url])
        if self._system == "linux":
            return self._cmd.run(["xdg-open", url])
        return self._cmd.run(["cmd", "/c", "start", "", url])

    def navigate(self, url: str, *, browser: str | None = None) -> dict[str, Any]:
        if browser and self._system == "darwin":
            return self._cmd.run(["open", "-a", browser, url])
        return self.open_url(url)
