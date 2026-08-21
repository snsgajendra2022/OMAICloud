"""Freshness routing — decide when live retrieval should run (not an LLM)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_TIME_SENSITIVE = re.compile(
    r"\b("
    r"latest\s+\w+|current\s+\w+|today|tonight|yesterday|this\s+week|this\s+month|"
    r"right\s+now|as\s+of|breaking|news|release\s+notes|changelog|"
    r"who\s+is\s+the\s+current|prime\s+minister|president|head\s+of\s+state|"
    r"stock\s+price|weather|score|election|up[\s-]?to[\s-]?date|"
    r"what\s+happened|recently|this\s+year|202[4-9]|203\d"
    r")\b",
    re.IGNORECASE,
)

_FACTUAL = re.compile(
    r"\b("
    r"what\s+is|what\s+are|who\s+is|who\s+was|when\s+was|when\s+did|"
    r"where\s+is|where\s+was|why\s+did|why\s+is|which|"
    r"explain|define|meaning\s+of|capital\s+of|history\s+of|"
    r"team|match|game|player|coach|champion|"
    r"basketball|nba|nfl|mlb|soccer|football|cricket|world\s+cup|"
    r"company|ceo|founded|invented"
    r")\b",
    re.IGNORECASE,
)

_HOW_FACT = re.compile(
    r"\bhow\s+(?:to|do|does|did|can|could|much|many|long|far|old|big|"
    r"work|works|make|build|install|fix)\b",
    re.IGNORECASE,
)

_OM_SELF = re.compile(
    r"\b("
    r"what\s+can\s+you\s+do|what\s+do\s+you\s+do|what\s+are\s+you|who\s+are\s+you|"
    r"your\s+capabilities|what\s+can\s+om|about\s+you|about\s+om\b|"
    r"local\s+om|om[\s-]?1\.?0|om\s+model|om\s+ai\b|"
    r"are\s+you\s+chatgpt|are\s+you\s+ollama|third[\s-]?party|external\s+llm|"
    r"what\s+is\s+om\b|tell\s+me\s+about\s+om"
    r")\b",
    re.IGNORECASE,
)

# Optional friendly nicknames after a greeting (bhai, bro, yaar, …).
_FRIENDLY = (
    r"(?:\s+(?:bhai|bro|yaar|dude|mate|friend|ji|sir|mam|maam|boss|dear))?"
)

_CHITCHAT_FULL = re.compile(
    r"^("
    r"hi+|hello|hey+|yo|sup|namaste|salaam|salam|"
    r"thanks|thank you|ok|okay|bye|goodbye|"
    r"good mor\w*|good afternoon|good evening|good night|"
    r"(?:good mor\w* )?how are you(?: doing)?|"
    r"how(?: s| is)? it going|"
    r"what(?: s| is)? up|"
    r"who are you|"
    r"what(?: s| is)? your name|"
    r"nice to meet you"
    r")"
    + _FRIENDLY
    + r"$",
    re.IGNORECASE,
)

# Starts like a greeting even if extra short words follow.
_GREETING_START = re.compile(
    r"^(hi+|hello|hey+|yo|sup|namaste|salaam|salam|"
    r"good\s+mor\w*|good\s+afternoon|good\s+evening|good\s+night)\b",
    re.IGNORECASE,
)


def _normalize_chat(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.replace("'", " ").replace("’", " ").replace("`", " ")
    t = re.sub(r"[^\w\s]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_chitchat(text: str) -> bool:
    """Greetings / small talk — never web search."""
    cleaned = _normalize_chat(text)
    if not cleaned or len(cleaned) > 100:
        return False
    return bool(_CHITCHAT_FULL.match(cleaned))


def is_greeting_like(text: str) -> bool:
    """Loose greeting detector (e.g. 'good morning bhai'). Never retrieve for these."""
    if is_chitchat(text):
        return True
    cleaned = _normalize_chat(text)
    if not cleaned or len(cleaned) > 100:
        return False
    return bool(_GREETING_START.match(cleaned)) and len(cleaned.split()) <= 8


def is_om_self_query(text: str) -> bool:
    """Questions about OM AI itself — answer natively, never Ollama web hits."""
    t = (text or "").strip()
    if not t or is_greeting_like(t):
        return False
    return bool(_OM_SELF.search(t))


def needs_live_knowledge(text: str) -> bool:
    """True only for world facts / news — not greetings or OM self-questions."""
    t = (text or "").strip()
    if not t or is_greeting_like(t) or is_om_self_query(t):
        return False
    if _TIME_SENSITIVE.search(t):
        return True
    if _HOW_FACT.search(t):
        return True
    if _FACTUAL.search(t):
        return True
    return False


def is_time_sensitive_query(text: str) -> bool:
    t = (text or "").strip()
    if not t or is_greeting_like(t):
        return False
    return bool(_TIME_SENSITIVE.search(t))


@dataclass
class FreshnessDecision:
    needs_live: bool
    reason: str
    query: str


class FreshnessRouter:
    """Route factual queries to retrieval; synthesis stays OM-1.0 (never another LLM)."""

    def decide(self, messages: list[dict], *, force: bool = False) -> FreshnessDecision:
        user_bits: list[str] = []
        for m in messages:
            if str(m.get("role") or "") == "user":
                user_bits.append(str(m.get("content") or ""))
        query = (user_bits[-1] if user_bits else "").strip()
        if not query:
            return FreshnessDecision(False, "empty_query", "")
        if is_greeting_like(query):
            return FreshnessDecision(False, "chitchat", query)
        if is_om_self_query(query):
            return FreshnessDecision(False, "om_self", query)
        # Never force web search for greetings; force is also ignored when disabled.
        if force and not is_greeting_like(query):
            return FreshnessDecision(True, "forced_retrieval", query)
        if is_time_sensitive_query(query):
            return FreshnessDecision(True, "time_sensitive", query)
        if needs_live_knowledge(query):
            return FreshnessDecision(True, "factual", query)
        return FreshnessDecision(False, "static_ok", query)
