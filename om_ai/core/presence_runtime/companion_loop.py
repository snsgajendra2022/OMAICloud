"""Companion living loop — phase transitions."""
from __future__ import annotations

import time
from typing import Any

from .attention_manager import AttentionManager
from .availability_state import AvailabilityState
from .idle_behavior import IdleBehavior
from .interruption_manager import InterruptionManager
from .session_lifecycle import SessionLifecycle


class CompanionLoop:
    """
    OM Started → Ready → Waiting → Listening → Thinking → Responding → Waiting
    """

    def __init__(self) -> None:
        self.phase = AvailabilityState.OFFLINE
        self.attention = AttentionManager()
        self.idle = IdleBehavior()
        self.interruptions = InterruptionManager()
        self.session = SessionLifecycle()
        self._waiting_since_ms = 0.0

    def boot(self) -> dict[str, Any]:
        self.phase = AvailabilityState.STARTING
        self.phase = AvailabilityState.READY
        return self._enter(AvailabilityState.WAITING)

    def on_listen_start(self) -> dict[str, Any]:
        return self._enter(AvailabilityState.LISTENING)

    def on_user_final(self) -> dict[str, Any]:
        self.session.on_user()
        return self._enter(AvailabilityState.THINKING)

    def on_respond_start(self) -> dict[str, Any]:
        return self._enter(AvailabilityState.RESPONDING)

    def on_respond_end(self) -> dict[str, Any]:
        self.session.on_assistant()
        return self._enter(AvailabilityState.WAITING)

    def on_interrupt(self) -> dict[str, Any]:
        pack = self.interruptions.fire()
        self.phase = AvailabilityState.INTERRUPTED
        out = self._enter(AvailabilityState.WAITING)
        out["interrupt"] = pack
        return out

    def tick(self) -> dict[str, Any]:
        if self.phase != AvailabilityState.WAITING:
            return {"phase": self.phase.value, "idle": None}
        idle = self.idle.tick(waiting_since_ms=self._waiting_since_ms)
        return {"phase": self.phase.value, "idle": idle, **self.attention.on_phase(self.phase)}

    def _enter(self, phase: AvailabilityState) -> dict[str, Any]:
        self.phase = phase
        if phase == AvailabilityState.WAITING:
            self._waiting_since_ms = time.time() * 1000
        attn = self.attention.on_phase(phase)
        return {
            "phase": phase.value,
            "state": phase.value,
            "attention": attn,
            "session": self.session.snapshot(),
            "alive": True,
        }
