"""Back-compat shim — use prosody_engine.ProsodyEngine."""
from __future__ import annotations

from .prosody_engine import ProsodyController, ProsodyEngine

__all__ = ["ProsodyEngine", "ProsodyController"]
