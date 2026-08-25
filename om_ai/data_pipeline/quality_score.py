"""Document quality scoring."""
from __future__ import annotations

from om_ai.corpus.filters import quality_score as _quality_score


def quality_score(text: str) -> float:
    return _quality_score(text)
