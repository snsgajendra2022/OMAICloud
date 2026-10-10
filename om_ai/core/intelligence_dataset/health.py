"""
OM Intelligence Dataset health checks.
"""

from __future__ import annotations

from typing import Any


class DatasetHealthChecker:

    def __init__(self, manager) -> None:
        self.manager = manager

    def check(self) -> dict[str, Any]:

        checks: dict[str, bool] = {}

        # Repository
        try:
            total = self.manager.count()
            checks["repository"] = True
        except Exception:
            total = 0
            checks["repository"] = False

        # Semantic index
        try:
            indexed = self.manager.indexed_count()
            checks["semantic_index"] = True
        except Exception:
            indexed = 0
            checks["semantic_index"] = False

        # Statistics
        try:
            stats = self.manager.stats()
            checks["statistics"] = True
        except Exception:
            stats = {}
            checks["statistics"] = False

        # Overall
        healthy = all(
            checks.values()
        )

        return {
            "healthy": healthy,
            "checks": checks,
            "total_items": total,
            "indexed_items": indexed,
            "stats": stats,
        }