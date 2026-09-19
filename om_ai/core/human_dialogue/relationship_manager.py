from __future__ import annotations
from typing import Any

class RelationshipManager:
    def __init__(self) -> None:
        self.address_as = "Sir"
        self.bond = 0.55

    def address(self, locale: str = "en") -> str:
        return "Sir" if locale != "hi" else "Sir"

    def to_dict(self) -> dict[str, Any]:
        return {"address_as": self.address_as, "bond": self.bond}
