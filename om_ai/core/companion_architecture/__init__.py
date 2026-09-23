"""OM AI Complete Companion System — final 13-layer architecture.

Canonical entry: CompanionPipeline.run(...)
Maps every architecture layer to real modules already in the repo.
"""
from __future__ import annotations

from .companion_pipeline import CompanionPipeline, get_companion_pipeline
from .layers import ARCHITECTURE_LAYERS, layer_status
from .checklist import production_checklist

__all__ = [
    "CompanionPipeline",
    "get_companion_pipeline",
    "ARCHITECTURE_LAYERS",
    "layer_status",
    "production_checklist",
]
