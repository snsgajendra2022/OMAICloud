"""Knowledge context hints by topic."""
from __future__ import annotations

from typing import Any


class KnowledgeContext:
    def for_topic(self, topic: str, message: str) -> dict[str, Any]:
        hints = {
            "voice_engine": "Stay focused on voice / TTS / STT companion work.",
            "avatar": "Stay focused on presence / lip sync / avatar.",
            "memory": "Use remembered preferences and prior discussion.",
            "coding": "Be precise; prefer concrete code guidance.",
            "project_om": "This is the OM companion / operating brain project.",
        }
        return {"topic": topic, "hint": hints.get(topic, ""), "message": (message or "")[:80]}
