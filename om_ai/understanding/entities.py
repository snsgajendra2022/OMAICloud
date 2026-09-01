"""Contextual entity / acronym expansion (meaning, not word-for-word)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class EntityHit:
    surface: str
    meaning: str
    context: str = ""
    confidence: float = 0.8


# Context-sensitive: short token + place/domain → meaning.
_CONTEXT_ACRONYMS: list[tuple[re.Pattern[str], str, str, str]] = [
    (
        re.compile(r"\b(pm|p\.m\.)\b", re.I),
        re.compile(r"\b(india|indian|bharat)\b", re.I),
        "Prime Minister",
        "India",
    ),
    (
        re.compile(r"\b(pm|p\.m\.)\b", re.I),
        re.compile(r"\b(uk|britain|united kingdom)\b", re.I),
        "Prime Minister",
        "United Kingdom",
    ),
    (
        re.compile(r"\bceo\b", re.I),
        re.compile(r"."),
        "Chief Executive Officer",
        "business",
    ),
    (
        re.compile(r"\bapi\b", re.I),
        re.compile(r"\b(python|fastapi|rest|backend|project)\b", re.I),
        "application programming interface",
        "software",
    ),
]


def expand_entities(text: str) -> list[EntityHit]:
    t = text or ""
    hits: list[EntityHit] = []
    for token_pat, ctx_pat, meaning, ctx in _CONTEXT_ACRONYMS:
        if token_pat.search(t) and ctx_pat.search(t):
            surface = token_pat.search(t).group(0)
            hits.append(EntityHit(surface=surface, meaning=meaning, context=ctx, confidence=0.92))
    return hits


def rewrite_with_entities(text: str) -> tuple[str, list[EntityHit]]:
    """Return a clarified string plus entity hits."""
    hits = expand_entities(text)
    out = text or ""
    for h in hits:
        if h.surface.lower() in {"pm", "p.m."} and h.context.lower() == "india":
            out = re.sub(
                r"\b(what\s+is\s+)?pm\b",
                "Prime Minister",
                out,
                count=1,
                flags=re.I,
            )
            if "india" in out.lower() and "prime minister" in out.lower():
                if not re.search(r"prime minister of india", out, re.I):
                    out = re.sub(
                        r"prime minister",
                        "Prime Minister of India",
                        out,
                        count=1,
                        flags=re.I,
                    )
    return out, hits
