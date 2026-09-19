from __future__ import annotations

from enum import Enum


class OnboardingStatus(str, Enum):
    CREATED = "created"
    PROFILE_READY = "profile_ready"
    ASSISTANT_READY = "assistant_ready"
    MEMORY_READY = "memory_ready"
    COMPLETED = "completed"
    FAILED = "failed"
