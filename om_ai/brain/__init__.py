"""OM Brain package — dataset-powered cognition over local corpora."""
from __future__ import annotations

from .dataset_engine import grounded_or_none, power_from_datasets, retrieve_answer, status

__all__ = [
    "power_from_datasets",
    "retrieve_answer",
    "grounded_or_none",
    "status",
]
