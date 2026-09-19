"""STEP 103 — Semantic facts about the user / world."""
from __future__ import annotations
from typing import Any

class SemanticMemory:
    def __init__(self) -> None:
        self.facts: dict[str, str] = {
            "user_name": "Gajendra",
            "active_project": "OM AI",
            "detail_preference": "detailed",
        }

    def set(self, key: str, value: str) -> None:
        self.facts[str(key)] = str(value)

    def get(self, key: str, default: str = "") -> str:
        return self.facts.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.facts)

    def observe(self, text: str) -> dict[str, Any]:
        low = (text or "").lower()
        if "detailed" in low or "deeply" in low:
            self.set("detail_preference", "detailed")
        if "short" in low or "brief" in low:
            self.set("detail_preference", "brief")
        if "om ai" in low or "om companion" in low:
            self.set("active_project", "OM AI")
        return self.to_dict()
