"""High-precision local facts (not a substitute for ingested corpora)."""
from __future__ import annotations

import re
from typing import Any


# Curated, testable facts. Expand via ingest for everything else.
_FACTS: list[dict[str, Any]] = [
    {
        "id": "pm-india",
        "patterns": [
            re.compile(r"\bpm\b.*\bindia\b|\bindia\b.*\bpm\b", re.I),
            re.compile(r"prime\s+minister.*india|india.*prime\s+minister", re.I),
            re.compile(r"what\s+is\s+pm\s+in\s+india", re.I),
        ],
        "answer": (
            "In India, **PM** means **Prime Minister** — the head of government "
            "of the Republic of India (not the President, who is head of state)."
        ),
        "entities": {"pm": "Prime Minister", "place": "India"},
        "domain": "civics",
    },
]


def lookup_fact(question: str) -> dict[str, Any] | None:
    q = (question or "").strip()
    if not q:
        return None
    for fact in _FACTS:
        if any(p.search(q) for p in fact["patterns"]):
            return {
                "id": fact["id"],
                "answer": fact["answer"],
                "entities": fact["entities"],
                "domain": fact["domain"],
                "source": "om_fact_table",
            }
    return None
