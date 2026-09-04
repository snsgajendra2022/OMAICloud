"""
OM Multilingual Knowledge Intelligence (STEP 80.12)

Language → Meaning → Knowledge Retrieval → Reasoning → Same-Language Reply

Detects language, extracts normalized meaning (topic / country / intent),
and builds a retrieval query that works across languages.
"""
from __future__ import annotations

import re
from typing import Any


# Lightweight cross-lingual cue maps (expandable; no external API required)
_TOPIC_CUES: dict[str, tuple[str, ...]] = {
    "artificial intelligence": (
        "ai",
        "artificial intelligence",
        "machine learning",
        "ml",
        "एआई",
        "ए आई",
        "आर्टिफिशियल",
        "कृत्रिम बुद्धिमत्ता",
        "ai का",
        "ai के",
    ),
    "software engineering": (
        "code",
        "coding",
        "programming",
        "software",
        "developer",
        "कोड",
        "प्रोग्राम",
        "सॉफ्टवेयर",
    ),
    "web development": (
        "react",
        "laravel",
        "fastapi",
        "website",
        "frontend",
        "backend",
        "वेबसाइट",
        "वेब",
    ),
    "business": (
        "business",
        "startup",
        "market",
        "revenue",
        "व्यवसाय",
        "बिज़नेस",
        "बाजार",
    ),
    "education": ("school", "university", "exam", "शिक्षा", "स्कूल", "विश्वविद्यालय"),
}

_COUNTRY_CUES: dict[str, tuple[str, ...]] = {
    "India": ("india", "भारत", "bharat", "indian", "भारतीय"),
    "United States": ("usa", "united states", "america", "अमेरिका", "यूएसए"),
    "United Kingdom": ("uk", "britain", "england", "ब्रिटेन"),
    "Japan": ("japan", "जापान"),
    "China": ("china", "चीन"),
}

_INTENT_CUES: dict[str, tuple[str, ...]] = {
    "future_analysis": (
        "future",
        "will",
        "outlook",
        "prediction",
        "भविष्य",
        "आगे",
        "क्या होगा",
    ),
    "explanation": ("what is", "explain", "क्या है", "समझाओ", "मतलब"),
    "how_to": ("how to", "steps", "kaise", "कैसे", "बनाओ", "build"),
    "comparison": ("vs", "versus", "compare", "तुलना", "अंतर"),
    "recommendation": ("best", "should i", "recommend", "सुझाव", "सबसे अच्छा"),
}


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def extract_meaning(text: str, *, language: str = "en") -> dict[str, Any]:
    """Extract cross-lingual meaning: topic, country, intent, retrieval query."""
    raw = text or ""
    low = _norm(raw)

    topics: list[str] = []
    for topic, cues in _TOPIC_CUES.items():
        if any(c in low or c in raw for c in cues):
            topics.append(topic)

    countries: list[str] = []
    for country, cues in _COUNTRY_CUES.items():
        if any(c in low or c in raw for c in cues):
            countries.append(country)

    intent = "general"
    intent_score = 0
    for name, cues in _INTENT_CUES.items():
        hits = sum(1 for c in cues if c in low or c in raw)
        if hits > intent_score:
            intent_score = hits
            intent = name

    # Latin / Devanagari token harvest for retrieval
    tokens = re.findall(r"[A-Za-z]{3,}|[\u0900-\u097F]{2,}", raw)
    # Prefer English topic labels for knowledge retrieval
    retrieval_parts = list(topics) + list(countries)
    if intent != "general":
        retrieval_parts.append(intent.replace("_", " "))
    # Keep distinctive English tokens from the query
    for t in tokens:
        if t.isascii() and t.lower() not in {"the", "and", "for", "what", "with"}:
            retrieval_parts.append(t)
    retrieval_query = " ".join(dict.fromkeys(retrieval_parts)).strip() or raw

    return {
        "language": language,
        "topic": topics[0] if topics else None,
        "topics": topics,
        "country": countries[0] if countries else None,
        "countries": countries,
        "intent": intent,
        "retrieval_query": retrieval_query,
        "normalized_english": retrieval_query,
    }


class MultilingualKnowledge:
    """Language → Meaning → Knowledge Retrieval helper."""

    def understand(self, text: str, *, language: str = "en") -> dict[str, Any]:
        meaning = extract_meaning(text, language=language)
        knowledge_hits: list[dict[str, Any]] = []
        try:
            from om_ai.knowledge.retrieval import search_knowledge

            q = meaning.get("retrieval_query") or text
            raw = search_knowledge(str(q), k=5) or []
            for h in raw:
                if isinstance(h, dict):
                    knowledge_hits.append(h)
                else:
                    knowledge_hits.append({"content": str(h)})
        except Exception:
            try:
                from om_ai.agent.tools import search_knowledge as sk

                q = meaning.get("retrieval_query") or text
                snippets = sk(str(q), k=5) or []
                for s in snippets:
                    if isinstance(s, dict):
                        knowledge_hits.append(s)
                    else:
                        knowledge_hits.append({"content": str(s)})
            except Exception:
                knowledge_hits = []

        return {
            "meaning": meaning,
            "knowledge": knowledge_hits,
            "knowledge_text": "\n".join(
                str(h.get("content") or h.get("answer") or h.get("text") or "")[:400]
                for h in knowledge_hits[:4]
                if h
            ).strip(),
        }
