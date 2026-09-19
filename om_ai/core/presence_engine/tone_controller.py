from __future__ import annotations

class ToneController:
    def for_state(self, state: str) -> dict:
        s = (state or "WAITING").upper()
        if s == "CONCERNED":
            return {"pace": "slow", "warmth": 0.9, "energy": 0.35}
        if s == "HAPPY":
            return {"pace": "bright", "warmth": 0.8, "energy": 0.85}
        if s == "THINKING":
            return {"pace": "measured", "warmth": 0.5, "energy": 0.4}
        if s == "EXPLAINING":
            return {"pace": "clear", "warmth": 0.6, "energy": 0.55}
        return {"pace": "calm", "warmth": 0.65, "energy": 0.45}
