from __future__ import annotations
from typing import Any

class CameraManager:
    def status(self) -> dict[str, Any]:
        return {"available": False, "reason": "camera_opt_in_required", "devices": []}

    def capture(self) -> dict[str, Any]:
        return {"ok": False, "reason": "camera_disabled_by_default"}
