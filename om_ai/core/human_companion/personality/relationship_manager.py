"""Relationship manager."""
from __future__ import annotations

from typing import Any


class RelationshipManager:
    def assess(self, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        name = str((profile or {}).get("name") or "").strip()
        return {
            "address": "bhai",
            "known_name": name,
            "style": "brother_companion",
            "bond": "brother",
            "care": "high",
        }
