from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeContext:

    query: str

    concepts: list[str] = field(
        default_factory=list
    )

    matched_nodes: list[Any] = field(
        default_factory=list
    )

    confidence: float = 0.0

    source: str = "internal"

    knowledge_found: bool = False

    missing_information: list[str] = field(
        default_factory=list
    )