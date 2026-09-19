from typing import Any


class LipSync:
    def plan(self, text: str) -> dict[str, Any]:
        # Approximate viseme frames for presence3d (seconds)
        words = max(1, len((text or "").split()))
        dur = max(0.6, words * 0.28)
        frames = []
        t = 0.0
        step = dur / max(4, words)
        for i in range(max(4, words)):
            frames.append({"t": round(t, 3), "jaw": 0.08 + (0.12 if i % 2 == 0 else 0.04)})
            t += step
        frames.append({"t": round(dur, 3), "jaw": 0.02})
        return {"frames": frames, "duration": dur}
