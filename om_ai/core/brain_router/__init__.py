"""STEP 24 — OM Brain Router.

Connects Intelligence Fusion + Deep Research + Knowledge Brain + Agents
into one production flow:

  User
    → OM Brain
    → Intelligence Fusion
    → Research
    → Knowledge
    → Agents
    → Response
"""
from __future__ import annotations

from .om_brain_router import OMBrainRouter, run_om_brain_router

__all__ = [
    "OMBrainRouter",
    "run_om_brain_router",
]
