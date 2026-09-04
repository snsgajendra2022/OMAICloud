"""Structured meaning from raw text — schema affinity, not keyword if/else."""
from __future__ import annotations

import math
import re
from typing import Any


# Intent schemas: characteristic tokens + required co-occurrence groups.
# New intents are added as schema rows — never as if topic: branches.
INTENT_SCHEMAS: list[dict[str, Any]] = [
    {
        "intent": "vision_analysis",
        "action": "analyze_image",
        "domain": "vision",
        "tokens": {"image", "screenshot", "photo", "diagram", "chart", "ui", "ocr", "picture", "upload"},
        "boost_pairs": [("analyze", "image"), ("what", "image"), ("extract", "data"), ("improve", "design")],
        "soft": {"dashboard", "invoice", "wrong", "similar"},
    },
    {
        "intent": "date_request",
        "action": "retrieve",
        "domain": "time",
        # Calendar asks only — bare "day"/"date"/"today" are too noisy
        # ("how was your day/date" is social, not a calendar request).
        "tokens": {"clock", "timezone", "calendar"},
        "boost_pairs": [
            ("today", "date"),
            ("current", "date"),
            ("what", "date"),
            ("what", "time"),
            ("todays", "date"),
            ("current", "time"),
            ("what", "day"),
        ],
        "require_pair": True,
    },
    {
        "intent": "conversation",
        "action": "chat",
        "domain": "social",
        "tokens": {
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank",
            "namaste",
            "yo",
            "morning",
            "moring",  # common typo
            "evening",
            "afternoon",
            "good",
            "how",
            "was",
            "your",
            "day",
            "night",
            "going",
        },
        "boost_pairs": [
            ("good", "morning"),
            ("good", "moring"),
            ("good", "evening"),
            ("good", "afternoon"),
            ("how", "day"),
            ("how", "date"),  # "how was your date" = social outing, not calendar
            ("how", "going"),
            ("how", "you"),
        ],
    },
    {
        "intent": "prompt_generation",
        "action": "create_prompt",
        "domain": "software",
        "tokens": {"prompt", "master", "cursor", "system", "instruction", "template"},
        "boost_pairs": [("create", "prompt"), ("make", "prompt"), ("write", "prompt"), ("generate", "prompt")],
        "soft": {"react", "code", "app", "ai"},
    },
    {
        "intent": "recommendation",
        "action": "generate_playlist",
        "domain": "music",
        "tokens": {"playlist", "music", "song", "songs", "track", "spotify", "recommend", "suggestion", "name"},
        "boost_pairs": [("music", "playlist"), ("playlist", "name"), ("song", "recommend")],
        "soft": {"coding", "workout", "relax", "focus"},
    },
    {
        "intent": "code_creation",
        "action": "implement",
        "domain": "software",
        "tokens": {"create", "build", "implement", "app", "api", "component", "page", "login", "dashboard"},
        "soft": {"react", "python", "laravel", "fastapi", "code"},
        "exclude_if": {"prompt"},
    },
    {
        "intent": "explanation",
        "action": "explain",
        "domain": "knowledge",
        "tokens": {"explain", "what", "why", "how", "describe", "mean", "definition"},
        "soft": {"is", "does", "about"},
    },
    {
        "intent": "debugging",
        "action": "fix",
        "domain": "software",
        "tokens": {"debug", "fix", "error", "bug", "crash", "traceback", "broken", "failing"},
    },
    {
        "intent": "research",
        "action": "research",
        "domain": "research",
        "tokens": {"research", "study", "investigate", "paper", "sources", "survey"},
    },
    {
        "intent": "planning",
        "action": "plan",
        "domain": "general",
        "tokens": {"plan", "roadmap", "steps", "strategy", "schedule"},
    },
    {
        "intent": "comparison",
        "action": "compare",
        "domain": "general",
        "tokens": {"compare", "versus", "vs", "difference", "better", "worse"},
    },
    {
        "intent": "calculation",
        "action": "calculate",
        "domain": "math",
        "tokens": {"calculate", "compute", "sum", "percent", "percentage", "math"},
    },
    {
        "intent": "question",
        "action": "answer",
        "domain": "general",
        "tokens": {"who", "when", "where", "which", "can", "should"},
    },
]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", (text or "").lower()))


def _pair_hit(tokens: set[str], a: str, b: str) -> bool:
    return a in tokens and b in tokens


def _is_social_checkin(text: str) -> bool:
    """True for 'how was your day/date' style chat — not calendar asks."""
    t = (text or "").strip().lower()
    if not t:
        return False
    if re.search(
        r"\bhow\s+(was|is|are|'s)\s+(your\s+)?(day|date|night|evening|morning)\b",
        t,
    ):
        return True
    if re.search(r"\bhow\s+are\s+you\b", t) or re.search(r"\bhow's\s+it\s+going\b", t):
        return True
    # good morning/evening + optional rest of sentence
    if re.match(
        r"^good\s+(morning|moring|evening|afternoon)\b",
        t,
    ):
        # Only treat as social if NOT asking for the calendar date
        if not re.search(
            r"\b(what(?:'s|\s+is)\s+(?:the\s+)?date|today'?s\s+date|current\s+date)\b",
            t,
        ):
            return True
    return False


class UnderstandingEngine:
    def understand(self, text: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = (text or "").strip()
        # Normalize common greeting typos before intent scoring
        norm = re.sub(r"\bmoring\b", "morning", raw, flags=re.I)
        norm = re.sub(r"\bafernoon\b", "afternoon", norm, flags=re.I)
        # Social check-ins — never calendar tools
        if _is_social_checkin(norm) or _is_social_checkin(raw):
            return {
                "intent": "conversation",
                "action": "chat",
                "domain": "social",
                "confidence": 0.96,
                "raw": raw,
                "tokens": sorted(_tokens(norm)),
                "needs_clarification": False,
            }
        # Greetings like hi / hii / hello — never "unclear" → empty reply
        if re.match(
            r"^(hi+|hello+|hey+|yo|sup|namaste|hola)(\s+there)?[!?.]*$",
            raw,
            re.I,
        ) or re.match(
            r"^(good\s+(morning|evening|afternoon))\b",
            norm,
            re.I,
        ):
            return {
                "intent": "conversation",
                "action": "chat",
                "domain": "social",
                "confidence": 0.95,
                "raw": raw,
                "tokens": sorted(_tokens(norm)),
                "needs_clarification": False,
            }

        toks = _tokens(norm)
        # Normalize elongated hi (hii → hi) for schema overlap
        toks |= {re.sub(r"(.)\1{2,}", r"\1\1", t) for t in toks}
        if any(re.fullmatch(r"hi+", t) for t in toks):
            toks.add("hi")
        ctx = context or {}
        ranked: list[tuple[float, dict[str, Any]]] = []

        for schema in INTENT_SCHEMAS:
            exclude = set(schema.get("exclude_if") or [])
            if exclude and exclude & toks:
                continue
            score = 0.0
            overlap = toks & set(schema["tokens"])
            score += 1.4 * len(overlap)
            soft = toks & set(schema.get("soft") or [])
            score += 0.45 * len(soft)
            pair_hits = 0
            for a, b in schema.get("boost_pairs") or []:
                if _pair_hit(toks, a, b):
                    score += 2.2
                    pair_hits += 1
            # Calendar intents must hit a boost pair (what+date, today+date, …)
            if schema.get("require_pair") and pair_hits < 1:
                continue
            if schema.get("require_pair") and pair_hits >= 1:
                score += 1.5  # strong calendar signal
            # Context soft prior (project mentions) without keyword routing
            hint = str(ctx.get("project_hint") or "").lower()
            if hint and any(h in hint for h in ("react", "om", "ai", "code")):
                if schema["intent"] in {"prompt_generation", "code_creation"}:
                    score += 0.35
            if score > 0:
                ranked.append((score, schema))

        if not ranked:
            return {
                "intent": "unclear",
                "action": "clarify",
                "domain": "general",
                "confidence": 0.25,
                "raw": raw,
                "tokens": sorted(toks),
                "needs_clarification": True,
            }

        ranked.sort(key=lambda x: x[0], reverse=True)
        best_score, best = ranked[0]
        second = ranked[1][0] if len(ranked) > 1 else 0.0
        # Confidence from margin + absolute score
        conf = 1.0 / (1.0 + math.exp(-(best_score - 1.5)))
        if best_score - second < 0.6:
            conf *= 0.75
        conf = round(min(0.99, max(0.2, conf)), 3)

        domain = best["domain"]
        # Prompt + software soft tokens → keep software domain
        if best["intent"] == "explanation" and soft_domain(toks):
            domain = soft_domain(toks) or domain

        return {
            "intent": best["intent"],
            "action": best["action"],
            "domain": domain,
            "confidence": conf,
            "raw": raw,
            "tokens": sorted(toks),
            "alternates": [
                {"intent": s["intent"], "score": round(sc, 3)}
                for sc, s in ranked[1:4]
            ],
            "needs_clarification": conf < 0.55 or best["intent"] == "unclear",
        }


def soft_domain(toks: set[str]) -> str | None:
    domains = {
        "software": {"react", "python", "code", "api", "app", "laravel", "git"},
        "music": {"music", "playlist", "song"},
        "time": {"date", "time", "today"},
        "science": {"quantum", "physics", "biology"},
        "business": {"business", "sales", "revenue"},
    }
    best = None
    best_n = 0
    for name, bag in domains.items():
        n = len(toks & bag)
        if n > best_n:
            best_n = n
            best = name
    return best if best_n else None
