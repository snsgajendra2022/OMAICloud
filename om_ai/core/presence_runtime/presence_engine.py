"""Presence engine — single entry for the living loop (STEP 64)."""
from __future__ import annotations

from typing import Any, Callable

from .availability_state import AvailabilityState
from .companion_loop import CompanionLoop

# Re-export name used by package
PresencePhase = AvailabilityState

_ENGINE: "PresenceEngine | None" = None


class PresenceEngine:
    def __init__(self) -> None:
        self.loop = CompanionLoop()
        # Optional bridge to older presence_engine expression layer
        self._legacy = None
        try:
            from om_ai.core.presence_engine import get_presence_runtime

            self._legacy = get_presence_runtime()
        except Exception:
            self._legacy = None

    def start(self) -> dict[str, Any]:
        return self.loop.boot()

    def bind_stop_speech(self, fn: Callable[[], None] | None) -> None:
        self.loop.interruptions.bind_stop(fn)

    def listening(self) -> dict[str, Any]:
        return self.loop.on_listen_start()

    def thinking(self) -> dict[str, Any]:
        return self.loop.on_user_final()

    def responding(self) -> dict[str, Any]:
        return self.loop.on_respond_start()

    def waiting(self) -> dict[str, Any]:
        return self.loop.on_respond_end()

    def interrupt(self) -> dict[str, Any]:
        return self.loop.on_interrupt()

    def tick(self) -> dict[str, Any]:
        return self.loop.tick()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 64,
            "phase": self.loop.phase.value,
            "session": self.loop.session.snapshot(),
            "legacy_presence": bool(self._legacy),
        }


def get_presence_engine() -> PresenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = PresenceEngine()
    return _ENGINE
