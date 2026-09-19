from __future__ import annotations
from typing import Any

class LipSync:
    def envelope(self, text: str) -> dict[str, Any]:
        # Simple amplitude envelope for HUD / future mouth mesh
        n = max(1, len((text or "").split()))
        peaks = [0.2 + (i % 3) * 0.25 for i in range(min(n, 24))]
        return {"frames": peaks, "mode": "energy", "visemes": "approx"}
