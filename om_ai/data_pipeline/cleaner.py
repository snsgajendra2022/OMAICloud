"""Text cleaning stage."""
from __future__ import annotations

import re
import unicodedata


def clean_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.replace("\x00", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()
