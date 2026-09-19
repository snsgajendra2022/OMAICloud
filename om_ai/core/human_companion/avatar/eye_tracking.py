from typing import Any


class EyeTracking:
    def plan(self, mode: str) -> dict[str, Any]:
        return {"look": "user", "blink_rate": 0.2 if mode == "speaking" else 0.35, "mode": mode}
