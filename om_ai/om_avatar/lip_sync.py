from __future__ import annotations

from typing import Any


class LipSync:
    """OM 3D avatar lip sync — delegates to voice_engine LipSyncEngine."""

    def jaw_open(self, energy: float = 0.0, speaking: bool = False) -> float:
        if not speaking:
            return 0.02
        return max(0.04, min(0.35, 0.08 + float(energy) * 0.2))

    def from_text(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        try:
            from om_ai.core.voice_engine.lip_sync import LipSyncEngine

            return LipSyncEngine().from_text(text, emotion=emotion)
        except Exception:
            n = max(1, len((text or "").split()))
            peaks = [0.2 + (i % 3) * 0.25 for i in range(min(n, 24))]
            return {"frames": peaks, "mode": "energy", "visemes": "approx"}

    def envelope(self, text: str) -> dict[str, Any]:
        pack = self.from_text(text)
        peaks = pack.get("peaks") or [
            float(f.get("jaw", 0.1)) for f in (pack.get("frames") or []) if isinstance(f, dict)
        ]
        return {"frames": peaks, "mode": pack.get("mode", "energy"), "visemes": "approx", "lips": pack}
