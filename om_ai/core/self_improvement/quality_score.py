from __future__ import annotations
from typing import Any

class QualityScore:
    def score(self, analysis: dict[str, Any]) -> float:
        issues = analysis.get("issues") or []
        return max(0.0, 1.0 - 0.18 * len(issues))
