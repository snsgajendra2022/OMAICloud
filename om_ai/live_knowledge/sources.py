"""Configured live knowledge sources (URLs / local docs). Not LLM providers."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeSource:
    name: str
    kind: str  # url | local | rss
    locator: str
    enabled: bool = True


DEFAULT_SOURCES: list[KnowledgeSource] = [
    KnowledgeSource("om_docs", "local", "docs/", enabled=True),
]
