"""OM AI Operating Intelligence — JARVIS-style facade over existing subsystems.

Physical embodiment (electronics / sensors / robotics / twin) starts as
safe stubs. Digital brain modules bridge to real implementations.
"""
from __future__ import annotations

from .facade import OperatingIntelligence, run_cycle, capability_status

__all__ = ["OperatingIntelligence", "run_cycle", "capability_status"]
