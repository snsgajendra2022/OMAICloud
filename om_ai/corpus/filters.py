"""Corpus document filters: language, quality, toxicity heuristics, PII."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from om_ai.corpus.service import _detect_language, _scrub_pii


_TOXIC_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(kill yourself|kys)\b",
        r"\b(nigger|faggot)\b",  # slur blocklist for training hygiene
        r"\b(child\s*porn|csam)\b",
        r"\b(how to make a bomb)\b",
        r"\b(credit card number)\s*[:#]?\s*\d{13,16}\b",
    )
]

_SPAM_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"(buy now|click here|limited offer).{0,40}(buy now|click here)",
        r"(viagra|cialis)\s+(online|cheap)",
        r"\$\$\$+",
    )
]


@dataclass
class FilterDecision:
    ok: bool
    reason: str = ""
    language: str = "und"
    quality_score: float = 0.0
    pii_hits: list[str] | None = None
    text: str = ""


def quality_score(text: str) -> float:
    if not text:
        return 0.0
    t = unicodedata.normalize("NFKC", text)
    printable = sum(ch.isprintable() or ch in "\n\t" for ch in t) / max(1, len(t))
    words = re.findall(r"\w+", t.lower())
    unique = len(set(words)) / max(1, len(words))
    length = min(1.0, len(t) / 2000)
    # Punish extreme repetition
    if words:
        top = max(words.count(w) for w in set(words))
        rep = top / len(words)
    else:
        rep = 1.0
    score = 0.45 * printable + 0.30 * unique + 0.25 * length - 0.35 * max(0.0, rep - 0.15)
    return round(max(0.0, min(1.0, score)), 4)


def is_toxic(text: str) -> bool:
    sample = text[:8000]
    return any(p.search(sample) for p in _TOXIC_PATTERNS)


def is_spammy(text: str) -> bool:
    sample = text[:4000]
    if any(p.search(sample) for p in _SPAM_PATTERNS):
        return True
    urls = sample.lower().count("http://") + sample.lower().count("https://")
    return urls > 35


def filter_document(
    text: str,
    *,
    min_chars: int = 80,
    min_quality: float = 0.35,
    allowed_languages: set[str] | None = None,
    scrub_pii: bool = True,
) -> FilterDecision:
    """Return cleaned text + accept/reject decision for training inclusion."""
    allowed_languages = allowed_languages or {"en", "mixed", "unicode", "und", "unknown"}
    raw = (text or "").strip()
    if len(raw) < min_chars:
        return FilterDecision(False, f"too_short:{len(raw)}", text=raw)
    if is_toxic(raw):
        return FilterDecision(False, "toxic", text=raw)
    if is_spammy(raw):
        return FilterDecision(False, "spam", text=raw)

    cleaned = unicodedata.normalize("NFKC", raw).replace("\x00", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    pii_hits: list[str] = []
    if scrub_pii:
        cleaned, pii_hits = _scrub_pii(cleaned)

    lang = _detect_language(cleaned)
    if lang not in allowed_languages and "en" in allowed_languages and lang == "unicode":
        # Keep multilingual unicode if explicitly wanted; default allows unicode
        pass
    if lang not in allowed_languages:
        return FilterDecision(False, f"lang:{lang}", language=lang, text=cleaned, pii_hits=pii_hits)

    q = quality_score(cleaned)
    if q < min_quality:
        return FilterDecision(False, f"quality:{q}", language=lang, quality_score=q, text=cleaned, pii_hits=pii_hits)

    return FilterDecision(
        True,
        "",
        language=lang,
        quality_score=q,
        pii_hits=pii_hits,
        text=cleaned,
    )
