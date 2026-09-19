"""STEP 51 runtime entry."""
from __future__ import annotations

from typing import Any

from .presence_manager import PresenceManager

_RUNTIME: PresenceRuntime | None = None


class PresenceRuntime:
    def __init__(self) -> None:
        self.manager = PresenceManager()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 51, "name": "Presence Intelligence", **self.manager.snapshot()}

    def react(self, text: str, **kwargs: Any) -> dict[str, Any]:
        return self.manager.react_to_user(text, **kwargs)

    def set_mode(self, mode: str, **kwargs: Any) -> dict[str, Any]:
        return self.manager.set_mode(mode, **kwargs)

    def thinking(self) -> dict[str, Any]:
        return self.manager.on_thinking()

    def speaking(self) -> dict[str, Any]:
        return self.manager.on_speaking()

    def listening(self) -> dict[str, Any]:
        return self.manager.on_listening()


def get_presence_runtime() -> PresenceRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = PresenceRuntime()
    return _RUNTIME
