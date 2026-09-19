"""Session mood / emotional climate for presence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MoodContext:
    label: str = "neutral"
    valence: float = 0.0
    arousal: float = 0.35
    trust: float = 0.6
    history: list[str] = field(default_factory=list)

    def update(self, *, label: str = "", valence: float | None = None, arousal: float | None = None) -> None:
        if label:
            self.label = label
            self.history.append(label)
            self.history = self.history[-24:]
        if valence is not None:
            self.valence = max(-1.0, min(1.0, valence))
        if arousal is not None:
            self.arousal = max(0.0, min(1.0, arousal))

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "trust": round(self.trust, 3),
        }
