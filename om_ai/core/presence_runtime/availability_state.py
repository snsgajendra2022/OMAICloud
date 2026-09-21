"""Availability states for the living companion."""
from __future__ import annotations

from enum import Enum


class AvailabilityState(str, Enum):
    OFFLINE = "offline"
    STARTING = "starting"
    READY = "ready"
    WAITING = "waiting"
    LISTENING = "listening"
    THINKING = "thinking"
    RESPONDING = "responding"
    INTERRUPTED = "interrupted"
    BUSY = "busy"
    MUTED = "muted"
