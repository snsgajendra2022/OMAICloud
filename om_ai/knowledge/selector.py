"""Knowledge Selection System — keep what matters for the user's goal."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeProfile:
    topic: str
    important: list[str] = field(default_factory=list)
    not_important: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "important": self.important,
            "not_important": self.not_important,
            "kept": self.kept,
            "dropped": self.dropped,
            "meta": self.meta,
        }


_PROFILES: list[tuple[re.Pattern[str], str, list[str], list[str]]] = [
    (
        re.compile(r"\breact\b.*\bdashboard\b|\bdashboard\b.*\breact\b", re.I),
        "react_dashboard",
        [
            "React components",
            "Layout",
            "State management",
            "Charts",
            "CSS",
            "API integration",
        ],
        ["History of React creation", "Jordan Walke biography", "Facebook open-source timeline"],
    ),
    (
        re.compile(r"\b(login|sign\s*in|auth)\b", re.I),
        "auth_login",
        [
            "Auth UI",
            "Validation",
            "Session / JWT",
            "Password hashing",
            "Backend API",
            "Security (HTTPS, rate limits)",
        ],
        ["History of authentication protocols", "Origin of the word password"],
    ),
    (
        re.compile(r"\bdocker\b", re.I),
        "docker",
        ["Dockerfile", "Image build", "Compose", "Ports", "Volumes", "Deploy steps"],
        ["History of Docker Inc.", "Containerd origin story"],
    ),
    (
        re.compile(r"\b(slow|performance|latency)\b", re.I),
        "performance",
        [
            "Database queries",
            "Images / assets",
            "JS bundle size",
            "API latency",
            "Caching",
            "Server resources",
        ],
        ["History of web performance", "Generic hardware shopping guides"],
    ),
]

_HISTORY_NOISE = re.compile(
    r"\b(history of|invented by|was created in\s+\d{4}|biography|founded in)\b",
    re.I,
)
_HOWTO = re.compile(r"\b(how\s+to|create|make|build|implement|add)\b", re.I)


def _match_profile(question: str) -> tuple[str, list[str], list[str]]:
    q = question or ""
    for pat, name, important, drop in _PROFILES:
        if pat.search(q):
            return name, list(important), list(drop)
    return "general", [], ["Unrelated trivia", "Off-topic history"]


def select_knowledge(
    question: str,
    snippets: list[str] | None = None,
) -> KnowledgeProfile:
    """Pick relevant knowledge; drop history/trivia on how-to questions."""
    topic, important, not_important = _match_profile(question)
    howto = bool(_HOWTO.search(question or ""))
    kept: list[str] = []
    dropped: list[str] = []
    for raw in snippets or []:
        text = (raw or "").strip()
        if not text:
            continue
        noisy = bool(_HISTORY_NOISE.search(text))
        if howto and noisy:
            dropped.append(text[:240])
            continue
        # Prefer overlap with important topics when we have a profile.
        if important:
            low = text.lower()
            hits = sum(1 for item in important if item.split()[0].lower() in low)
            if hits == 0 and noisy:
                dropped.append(text[:240])
                continue
        kept.append(text)
    return KnowledgeProfile(
        topic=topic,
        important=important,
        not_important=not_important,
        kept=kept[:8],
        dropped=dropped[:6],
        meta={"howto": howto, "input_snippets": len(snippets or [])},
    )
