from __future__ import annotations
from typing import Any

class RelationshipEngine:
    """How OM addresses and relates to the user (Tony/Jarvis bond)."""

    def __init__(self) -> None:
        self.address = "Sir"
        self.warmth = 0.7
        self.loyalty = 0.9

    def address_line(self, locale: str = "en") -> str:
        if locale == "hi":
            return "sir"
        return "Sir"

    def bond_hint(self) -> str:
        return f"Address as {self.address}. Warmth={self.warmth:.1f}. Loyal companion tone."

    def to_dict(self) -> dict[str, Any]:
        return {"address": self.address, "warmth": self.warmth, "loyalty": self.loyalty}
