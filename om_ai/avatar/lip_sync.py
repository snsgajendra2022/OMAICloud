from __future__ import annotations
from typing import Any


class LipSync:
    def envelope(self, text: str) -> dict[str, Any]:
        try:
            from om_ai.core.voice_engine.lip_sync import LipSyncEngine

            return LipSyncEngine().envelope(text)
        except Exception:
            n = max(1, len((text or "").split()))
            peaks = [0.2 + (i % 3) * 0.25 for i in range(min(n, 24))]
            return {"frames": peaks, "mode": "energy", "visemes": "approx"}
