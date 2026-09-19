from __future__ import annotations
from typing import Any


class AttentionManager:
    """Where OM should put attention this turn."""

    def focus(self, awareness: dict[str, Any]) -> dict[str, Any]:
        cues = set(awareness.get("cues") or [])
        if "user_distress" in cues:
            return {"primary": "empathy", "secondary": "listen", "priority": 1.0}
        if "time_task" in cues:
            return {"primary": "schedule", "secondary": "confirm", "priority": 0.9}
        if "visual_request" in cues:
            return {"primary": "vision", "secondary": "explain", "priority": 0.9}
        if "technical_work" in cues:
            return {"primary": "analyze", "secondary": "plan", "priority": 0.85}
        return {"primary": "converse", "secondary": "help", "priority": 0.5}
