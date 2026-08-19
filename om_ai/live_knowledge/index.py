"""Local document index helpers for live knowledge."""
from __future__ import annotations

from pathlib import Path

from om_ai.live_knowledge.search import LocalSearchIndex, index_text_files
from om_ai.live_knowledge.sources import local_roots


def build_empty_index() -> LocalSearchIndex:
    return LocalSearchIndex()


def build_default_index() -> LocalSearchIndex:
    idx = LocalSearchIndex()
    for root in local_roots():
        index_text_files(root, index=idx)
    return idx


def build_index_from_path(path: str | Path) -> LocalSearchIndex:
    return index_text_files(path, index=LocalSearchIndex())
