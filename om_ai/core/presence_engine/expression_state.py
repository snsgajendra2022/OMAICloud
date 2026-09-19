"""Maps presence + affect → avatar/voice expression cues."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .attention_state import PresenceMode


@dataclass
class ExpressionState:
    face: str = "neutral"
    eyes: str = "soft"
    motion: str = "idle_pulse"
    voice_energy: float = 0.5
    glow: float = 0.45

    def to_dict(self) -> dict[str, Any]:
        return {
            "face": self.face,
            "eyes": self.eyes,
            "motion": self.motion,
            "voice_energy": self.voice_energy,
            "glow": self.glow,
        }


_MAP = {
    PresenceMode.IDLE: ExpressionState("calm", "soft", "slow_drift", 0.35, 0.35),
    PresenceMode.ATTENTIVE: ExpressionState("engaged", "focused", "still_lean", 0.45, 0.55),
    PresenceMode.CURIOUS: ExpressionState("curious", "wide", "tilt", 0.55, 0.6),
    PresenceMode.THINKING: ExpressionState("thoughtful", "soft", "slow_pulse", 0.4, 0.5),
    PresenceMode.REMEMBERING: ExpressionState("recall", "search", "soft_spin", 0.4, 0.48),
    PresenceMode.EXPLAINING: ExpressionState("clear", "direct", "speak_pulse", 0.6, 0.65),
    PresenceMode.WAITING: ExpressionState("patient", "soft", "breathe", 0.35, 0.4),
    PresenceMode.CONFUSED: ExpressionState("puzzled", "narrow", "hesitate", 0.45, 0.5),
    PresenceMode.EXCITED: ExpressionState("bright", "wide", "quick_pulse", 0.75, 0.8),
    PresenceMode.CONCERNED: ExpressionState("soft_concern", "gentle", "slow_sway", 0.4, 0.45),
    PresenceMode.FOCUSED: ExpressionState("sharp", "locked", "stable", 0.5, 0.7),
    PresenceMode.SILENT_LISTENING: ExpressionState("receptive", "focused", "micro_move", 0.3, 0.5),
    PresenceMode.SPEAKING: ExpressionState("speaking", "contact", "energy_core", 0.7, 0.75),
}


def expression_for(mode: PresenceMode, *, mood: str = "neutral") -> ExpressionState:
    base = _MAP.get(mode, ExpressionState())
    if mood in {"concerned", "frustrated"} and mode not in {PresenceMode.EXCITED}:
        return ExpressionState("soft_concern", "gentle", base.motion, 0.38, base.glow)
    if mood in {"positive", "engaged_positive"}:
        return ExpressionState(base.face, base.eyes, base.motion, min(1.0, base.voice_energy + 0.1), min(1.0, base.glow + 0.1))
    return base
