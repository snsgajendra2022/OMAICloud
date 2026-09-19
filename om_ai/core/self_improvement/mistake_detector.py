from __future__ import annotations
from typing import Any

class MistakeDetector:
    def detect(self, analysis: dict[str, Any]) -> list[str]:
        return list(analysis.get("issues") or [])
