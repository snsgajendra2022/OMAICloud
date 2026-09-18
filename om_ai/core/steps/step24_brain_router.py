"""STEP 24 — OM Brain Router (fusion + research + knowledge + agents)."""
from __future__ import annotations

from om_ai.core.brain_router import OMBrainRouter, run_om_brain_router

__all__ = ["OMBrainRouter", "run_om_brain_router", "Step24BrainRouter"]


class Step24BrainRouter(OMBrainRouter):
    """Alias for roadmap naming."""

    step = 24
