"""Noise / transcript cleanup for STT text."""
from __future__ import annotations

import re


class NoiseFilter:
    def clean_transcript(self, text: str) -> str:
        t = (text or "").strip()
        t = re.sub(r"\b(uh+|um+|ah+|erm+)\b", " ", t, flags=re.I)
        t = re.sub(r"\s+", " ", t).strip(" ,.-")
        return t
