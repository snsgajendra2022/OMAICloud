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
            "of the Republic of India (not the President, who is head of state).\n\n"
            "The Prime Minister leads the Council of Ministers and runs the "
            "executive side of government."
        ),
        "entities": {"pm": "Prime Minister", "place": "India"},
        "domain": "civics",
    },
    {
        "id": "what-is-git",
        "patterns": [
            re.compile(r"\bwhat\s+is\s+git\b", re.I),
            re.compile(r"\b(try to|want to|how to).{0,24}\bgit\b", re.I),
            re.compile(r"\bexplain\s+git\b|\bgit\s+basics\b", re.I),
        ],
        "answer": (
            "**Git** is a version control system. It tracks changes in your files "
            "so you can save snapshots, switch between versions, and work with others "
            "without overwriting each other's work.\n\n"
            "Typical first steps:\n"
            "1. `git init` — start a repository\n"
            "2. `git add .` — stage files\n"
            "3. `git commit -m \"message\"` — save a snapshot\n"
            "4. `git status` — see what changed\n\n"
            "Git is the tool. **GitHub / GitLab / Bitbucket** are websites that host Git repos."
        ),
        "entities": {"git": "Git"},
        "domain": "software",
    },
    {
        "id": "what-is-react",
        "patterns": [
            re.compile(r"\bwhat\s+is\s+react\b", re.I),
            re.compile(r"^\s*react\s*\??\s*$", re.I),
            re.compile(r"\bexplain\s+react\b", re.I),
        ],
        "answer": (
            "**React** is a JavaScript library for building user interfaces. "
            "You split the UI into reusable **components**, each of which "
            "describes what should appear on screen.\n\n"
            "A component is a function that returns UI. When data (state) changes, "
            "React updates only the parts that need to change.\n\n"
            "People use React for web apps. **React Native** is a separate library "
            "that uses the same idea to build iOS and Android apps."
        ),
        "entities": {"react": "React"},
        "domain": "software",
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
