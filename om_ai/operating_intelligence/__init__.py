"""OM AI Operating Intelligence — Absolute Cognitive OS facade."""
from __future__ import annotations

from .facade import CycleResult, OperatingIntelligence, capability_status, run_cycle
from .manager import OMOperatingManager
from .core import OMCore

__all__ = [
    "CycleResult",
    "OperatingIntelligence",
    "run_cycle",
    "capability_status",
    "OMOperatingManager",
    "OMCore"
]
