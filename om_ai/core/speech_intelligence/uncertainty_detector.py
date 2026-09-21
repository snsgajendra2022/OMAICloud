"""Uncertainty / hesitation signals in speech text."""
from __future__ import annotations

import re
from typing import Any


class UncertaintyDetector:
    def detect(self, text: str) -> dict[str, Any]:
        t = (text or "").strip()
        low = t.lower()
        markers = []
        patterns = [
            (r"\bi don't know\b|\bmujhe nahi\b|\bpata nahi\b", "dont_know"),
            (r"\bmaybe\b|\bperhaps\b|\bshayad\b|\bmaybe\b", "hedge"),
            (r"\bi (was|am) (thinking|wondering|trying)\b|\bsoch raha\b", "thinking"),
            (r"\bum+\b|\buh+\b|\ber+\b|\ba+[a]+\b", "filler"),
            (r"\.\.\.|…", "ellipsis"),
            (r"\bbut\b.*$|\blekin\b", "contrast_open"),
        ]
        for pat, name in patterns:
            if re.search(pat, low):
                markers.append(name)
        score = min(1.0, 0.22 * len(markers) + (0.15 if len(t.split()) < 5 else 0))
        return {
            "uncertain": bool(markers) or score >= 0.35,
            "score": round(score, 3),
            "markers": markers,
            "prefer_listen": "dont_know" in markers or "thinking" in markers,
        }
