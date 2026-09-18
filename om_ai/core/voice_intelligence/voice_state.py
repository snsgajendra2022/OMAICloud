"""STEP 40 — Companion voice / runtime state machine."""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class CompanionState(str, Enum):
    STARTING = "STARTING"
    IDLE = "IDLE"
    LISTENING_FOR_WAKE_WORD = "LISTENING_FOR_WAKE_WORD"
    ACTIVATING = "ACTIVATING"
    LISTENING = "LISTENING"
    SPEECH_DETECTED = "SPEECH_DETECTED"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    THINKING = "THINKING"
    PLANNING = "PLANNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    EXECUTING_ACTION = "EXECUTING_ACTION"
    VERIFYING_ACTION = "VERIFYING_ACTION"
    GENERATING_RESPONSE = "GENERATING_RESPONSE"
    SPEAKING = "SPEAKING"
    INTERRUPTED = "INTERRUPTED"
    SLEEPING = "SLEEPING"
    MUTED = "MUTED"
    ERROR = "ERROR"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    READY = "READY"


# Allowed transitions (partial — unknown edges rejected)
_ALLOWED: dict[CompanionState, set[CompanionState]] = {
    CompanionState.STARTING: {CompanionState.READY, CompanionState.ERROR, CompanionState.SHUTTING_DOWN},
    CompanionState.READY: {
        CompanionState.IDLE,
        CompanionState.LISTENING_FOR_WAKE_WORD,
        CompanionState.LISTENING,
        CompanionState.MUTED,
        CompanionState.SHUTTING_DOWN,
    },
    CompanionState.IDLE: {
        CompanionState.LISTENING_FOR_WAKE_WORD,
        CompanionState.LISTENING,
        CompanionState.MUTED,
        CompanionState.SLEEPING,
        CompanionState.SHUTTING_DOWN,
    },
    CompanionState.LISTENING_FOR_WAKE_WORD: {
        CompanionState.ACTIVATING,
        CompanionState.MUTED,
        CompanionState.SLEEPING,
        CompanionState.ERROR,
        CompanionState.SHUTTING_DOWN,
    },
    CompanionState.ACTIVATING: {CompanionState.LISTENING, CompanionState.ERROR},
    CompanionState.LISTENING: {
        CompanionState.SPEECH_DETECTED,
        CompanionState.LISTENING_FOR_WAKE_WORD,
        CompanionState.MUTED,
        CompanionState.SLEEPING,
        CompanionState.SHUTTING_DOWN,
    },
    CompanionState.SPEECH_DETECTED: {CompanionState.TRANSCRIBING, CompanionState.LISTENING},
    CompanionState.TRANSCRIBING: {CompanionState.UNDERSTANDING, CompanionState.LISTENING, CompanionState.ERROR},
    CompanionState.UNDERSTANDING: {CompanionState.THINKING, CompanionState.PLANNING, CompanionState.GENERATING_RESPONSE},
    CompanionState.THINKING: {CompanionState.PLANNING, CompanionState.GENERATING_RESPONSE, CompanionState.WAITING_FOR_PERMISSION},
    CompanionState.PLANNING: {CompanionState.WAITING_FOR_PERMISSION, CompanionState.EXECUTING_ACTION, CompanionState.GENERATING_RESPONSE},
    CompanionState.WAITING_FOR_PERMISSION: {
        CompanionState.EXECUTING_ACTION,
        CompanionState.GENERATING_RESPONSE,
        CompanionState.LISTENING,
    },
    CompanionState.EXECUTING_ACTION: {CompanionState.VERIFYING_ACTION, CompanionState.ERROR, CompanionState.INTERRUPTED},
    CompanionState.VERIFYING_ACTION: {CompanionState.GENERATING_RESPONSE, CompanionState.PLANNING, CompanionState.ERROR},
    CompanionState.GENERATING_RESPONSE: {CompanionState.SPEAKING, CompanionState.LISTENING, CompanionState.INTERRUPTED},
    CompanionState.SPEAKING: {
        CompanionState.LISTENING,
        CompanionState.LISTENING_FOR_WAKE_WORD,
        CompanionState.INTERRUPTED,
        CompanionState.IDLE,
    },
    CompanionState.INTERRUPTED: {CompanionState.LISTENING, CompanionState.TRANSCRIBING, CompanionState.UNDERSTANDING},
    CompanionState.MUTED: {CompanionState.IDLE, CompanionState.LISTENING_FOR_WAKE_WORD, CompanionState.READY},
    CompanionState.SLEEPING: {CompanionState.LISTENING_FOR_WAKE_WORD, CompanionState.READY, CompanionState.IDLE},
    CompanionState.ERROR: {CompanionState.READY, CompanionState.IDLE, CompanionState.LISTENING_FOR_WAKE_WORD, CompanionState.SHUTTING_DOWN},
    CompanionState.SHUTTING_DOWN: set(),
}


def can_transition(src: CompanionState, dst: CompanionState) -> bool:
    if src == dst:
        return True
    allowed = _ALLOWED.get(src)
    if allowed is None:
        return True
    return dst in allowed


def assert_transition(src: CompanionState, dst: CompanionState) -> None:
    if not can_transition(src, dst):
        raise ValueError(f"Illegal companion state transition {src.value} → {dst.value}")
