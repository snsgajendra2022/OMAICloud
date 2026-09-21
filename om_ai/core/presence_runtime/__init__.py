"""STEP 64 — OM Presence Runtime (human-like living loop).

Ready → Waiting → Listening → Thinking → Responding → Waiting
"""
from __future__ import annotations

from .presence_engine import PresenceEngine, PresencePhase, get_presence_engine

__all__ = ["PresenceEngine", "PresencePhase", "get_presence_engine"]
