"""OM AI system diagnostics package."""
from __future__ import annotations

from .system_check import SystemHealthReport, run_system_check

__all__ = ["SystemHealthReport", "run_system_check"]
