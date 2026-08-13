"""Local document index stub for live knowledge."""
from __future__ import annotations

from om_ai.live_knowledge.search import LocalSearchIndex


def build_empty_index() -> LocalSearchIndex:
    return LocalSearchIndex()
