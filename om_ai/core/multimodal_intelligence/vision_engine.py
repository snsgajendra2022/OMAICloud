"""Vision engine — image / frame understanding hooks."""
from __future__ import annotations

from typing import Any


class VisionEngine:
    def understand(self, image_ref: str | bytes | None = None, *, hint: str = "") -> dict[str, Any]:
        if not image_ref and not hint:
            return {"has_vision": False, "summary": "", "objects": []}
        # Hook point for real vision models / OCR later
        return {
            "has_vision": True,
            "summary": hint or "Visual context attached.",
            "objects": [],
            "source": "stub_ready",
            "image_ref": str(image_ref)[:200] if image_ref and not isinstance(image_ref, bytes) else "bytes",
        }
