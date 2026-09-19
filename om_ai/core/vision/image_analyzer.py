from __future__ import annotations
from typing import Any

class ImageAnalyzer:
    def analyze(self, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "reason": "camera_or_screen_permission_required",
            "hint": "Grant screen/camera permission for Jarvis-class vision.",
            "meta": meta or {},
        }
