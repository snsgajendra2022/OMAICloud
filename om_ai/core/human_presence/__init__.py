"""STEP 71 — OM Human Presence Intelligence Layer.

Sits BEFORE SolutionEngine / ResponseEngine.

Purpose:
  Understand *why* the user said this, then decide *what* to answer.
  Companion behavior — not a search box.
  Empathy without pretending to be human.
  Search ≠ open. Action needs permission.
"""
from __future__ import annotations

from .presence_engine import HumanPresenceEngine, get_human_presence, run_human_presence

__all__ = [
    "HumanPresenceEngine",
    "get_human_presence",
    "run_human_presence",
]
