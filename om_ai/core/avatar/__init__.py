"""Avatar / Presence façade → presence_engine + human_companion.avatar."""
from __future__ import annotations

from typing import Any

__all__ = ["AvatarState", "ExpressionEngine", "LipSync", "GestureEngine", "map_state"]


def map_state(emotion: str = "neutral", *, phase: str = "listening") -> dict[str, Any]:
    from .avatar_state import AvatarState

    return AvatarState().resolve(emotion=emotion, phase=phase)
