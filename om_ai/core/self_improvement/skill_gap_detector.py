"""Detect skill gaps from conversation patterns."""
from __future__ import annotations

import re
from typing import Any


class SkillGapDetector:
    def detect(self, user_message: str, answer: str) -> dict[str, Any]:
        gaps: list[str] = []
        low_a = (answer or "").lower()
        low_u = (user_message or "").lower()
        if "i don't know" in low_a or "not sure" in low_a:
            gaps.append("knowledge")
        if "please complete your sentence" in low_a:
            gaps.append("incomplete_speech")
        if "how can i help you" in low_a:
            gaps.append("personality_robotic")
        if re.search(r"(?i)\b(code|bug|server)\b", low_u) and len(low_a.split()) < 4:
            gaps.append("technical_depth")
        return {"has_gap": bool(gaps), "gaps": gaps}
