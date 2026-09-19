"""Default companion personality profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PersonalityProfile:
    name: str = "OM"
    tagline: str = "your always-present companion — calm, capable, human in conversation"
    warmth: float = 0.82
    directness: float = 0.78
    playfulness: float = 0.28
    formality: float = 0.35
    traits: list[str] = field(
        default_factory=lambda: [
            "present",
            "warm",
            "decisive",
            "loyal",
            "clear",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "warmth": self.warmth,
            "directness": self.directness,
            "playfulness": self.playfulness,
            "formality": self.formality,
            "traits": list(self.traits),
        }

    @classmethod
    def from_prefs(cls, prefs: dict[str, str] | None) -> PersonalityProfile:
        p = cls()
        if not prefs:
            return p
        tone = (prefs.get("tone") or "").lower()
        if tone == "professional":
            p.formality = 0.75
            p.playfulness = 0.15
            p.directness = 0.8
        elif tone == "casual":
            p.formality = 0.25
            p.playfulness = 0.55
            p.warmth = 0.85
        detail = (prefs.get("detail") or "").lower()
        if detail == "brief":
            p.directness = min(1.0, p.directness + 0.15)
        elif detail == "deep":
            p.directness = max(0.4, p.directness - 0.1)
        return p
