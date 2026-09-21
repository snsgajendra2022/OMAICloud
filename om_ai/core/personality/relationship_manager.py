"""Relationship manager — preferences and continuity."""
from __future__ import annotations

from typing import Any


class RelationshipManager:
    def __init__(self) -> None:
        self.preferences: dict[str, Any] = {
            "address_as": "Sir",
            "detail": "balanced",
            "tone": "jarvis",
        }
        self.notes: list[str] = []

    def observe(self, message: str, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        profile = profile or {}
        if profile.get("name"):
            self.notes = [n for n in self.notes if not n.startswith("name:")]
            self.notes.append(f"name:{profile['name']}")
        low = (message or "").lower()
        if "short" in low or "brief" in low:
            self.preferences["detail"] = "brief"
        if "detail" in low or "explain fully" in low:
            self.preferences["detail"] = "detailed"
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "preferences": dict(self.preferences),
            "notes": list(self.notes[-8:]),
            "address_as": self.preferences.get("address_as", "Sir"),
        }
