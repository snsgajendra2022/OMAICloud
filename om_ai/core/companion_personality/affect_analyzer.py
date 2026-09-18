"""Semantic/heuristic affect from structure and intent confidence — not word lists."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class AffectState:
    valence: float
    arousal: float
    label: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "label": self.label,
            "confidence": round(self.confidence, 3),
        }


class AffectAnalyzer:
    """
    Estimate user affect from:
      - punctuation emphasis (!?, repeated ?)
      - message length vs recent average
      - intent confidence and intent class from upstream semantic layer
    """

    _MULTI_EXCL = re.compile(r"!{2,}")
    _MULTI_QUEST = re.compile(r"\?{2,}")
    _ELLIPSIS = re.compile(r"\.{3,}|…")

    def analyze(
        self,
        message: str,
        *,
        intent: str = "",
        intent_confidence: float = 0.5,
        history: list[dict[str, Any]] | None = None,
    ) -> AffectState:
        text = (message or "").strip()
        if not text:
            return AffectState(0.0, 0.1, "neutral", 0.9)

        valence = 0.0
        arousal = 0.35
        conf = 0.55 + min(0.35, intent_confidence * 0.35)

        excl = len(self._MULTI_EXCL.findall(text)) + text.count("!")
        quest = len(self._MULTI_QUEST.findall(text)) + text.count("?")
        if self._ELLIPSIS.search(text):
            valence -= 0.12
            arousal -= 0.08
            conf += 0.05

        if excl >= 2:
            arousal += 0.25
            valence += 0.08
        elif excl == 1:
            arousal += 0.12
            valence += 0.05

        if quest >= 2:
            arousal += 0.18
        elif quest == 1:
            arousal += 0.08

        words = max(1, len(text.split()))
        hist = history or []
        recent_lens = [
            len(str(h.get("content") or "").split())
            for h in hist[-6:]
            if h.get("role") == "user"
        ]
        avg = sum(recent_lens) / len(recent_lens) if recent_lens else float(words)
        if words > avg * 1.8:
            arousal += 0.15
        elif words < max(3.0, avg * 0.4):
            arousal -= 0.05

        intent_l = (intent or "").lower()
        if intent_l in {"thanks", "greeting", "morning", "afternoon", "evening"}:
            valence += 0.35
            arousal += 0.05
            conf = max(conf, 0.75)
        elif intent_l in {"goodbye"}:
            valence += 0.1
        elif intent_l in {"debugging", "troubleshooting"}:
            valence -= 0.15
            arousal += 0.12
            conf = max(conf, intent_confidence)
        elif intent_l in {"empty"}:
            valence = 0.0
            arousal = 0.1

        valence = max(-1.0, min(1.0, valence))
        arousal = max(0.0, min(1.0, arousal))
        label = self._label(valence, arousal)
        return AffectState(valence, arousal, label, min(0.98, conf))

    def _label(self, valence: float, arousal: float) -> str:
        if valence > 0.25 and arousal > 0.55:
            return "engaged_positive"
        if valence > 0.2:
            return "positive"
        if valence < -0.2 and arousal > 0.5:
            return "frustrated"
        if valence < -0.15:
            return "concerned"
        if arousal > 0.65:
            return "alert"
        if arousal < 0.25:
            return "calm"
        return "neutral"
