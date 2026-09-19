from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class AvatarState:
    pose: str = "idle"
    expression: str = "neutral"
    eyes: str = "soft"
    mouth_open: float = 0.0
    attention: float = 0.4
    glow: float = 0.45
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pose": self.pose,
            "expression": self.expression,
            "eyes": self.eyes,
            "mouth_open": self.mouth_open,
            "attention": self.attention,
            "glow": self.glow,
            "meta": dict(self.meta),
        }
