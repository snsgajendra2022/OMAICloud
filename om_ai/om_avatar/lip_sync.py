from __future__ import annotations

class LipSync:
    def jaw_open(self, energy: float = 0.0, speaking: bool = False) -> float:
        if not speaking:
            return 0.02
        return max(0.04, min(0.35, 0.08 + float(energy) * 0.2))
