"""OM-1.0 Genesis-JARVIS intelligence training package."""
from __future__ import annotations

from .domains import DOMAINS, GENESIS_SYSTEM, layers_catalog
from .generator import write_dataset

__all__ = ["DOMAINS", "GENESIS_SYSTEM", "layers_catalog", "write_dataset"]
