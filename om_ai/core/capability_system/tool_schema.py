"""Tool schema — normalized capability descriptors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolSchema:
    id: str
    name: str
    category: str
    description: str = ""
    risk: str = "low"  # low | medium | high
    requires_permission: bool = False
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "risk": self.risk,
            "requires_permission": self.requires_permission,
            "params": self.params,
        }
