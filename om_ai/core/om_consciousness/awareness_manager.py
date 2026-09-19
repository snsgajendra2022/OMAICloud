from __future__ import annotations
from typing import Any


class AwarenessManager:
    """What OM is currently aware of: user, context, environment cues."""

    def scan(self, text: str, *, memory_blob: str = "") -> dict[str, Any]:
        low = (text or "").lower()
        cues = []
        if any(k in low for k in ("tired", "thak", "bad day", "problem", "stuck")):
            cues.append("user_distress")
        if any(k in low for k in ("project", "code", "response", "quality", "bug")):
            cues.append("technical_work")
        if any(k in low for k in ("remind", "yaad", "kal", "tomorrow")):
            cues.append("time_task")
        if any(k in low for k in ("screen", "see", "camera", "dekh")):
            cues.append("visual_request")
        return {
            "cues": cues,
            "has_memory": bool(memory_blob.strip()),
            "memory_hint": (memory_blob or "")[:240],
            "input_len": len(text or ""),
        }
