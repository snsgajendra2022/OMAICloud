from __future__ import annotations
from typing import Any

class ImageUnderstanding:
    def describe(self, image_meta: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": False,
            "summary": "Vision model not attached yet — screen/camera hooks are ready.",
            "meta": image_meta or {},
        }
