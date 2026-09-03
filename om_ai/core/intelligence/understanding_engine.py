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
        "tokens": {"date", "today", "time", "day", "clock", "now", "current", "kal", "aaj"},
        "boost_pairs": [("today", "date"), ("current", "date"), ("what", "date"), ("what", "time")],
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
        "intent": "conversation",
        "action": "chat",
        "domain": "social",
        "tokens": {"hello", "hi", "hey", "thanks", "thank", "namaste", "yo"},
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


class UnderstandingEngine:
    def understand(self, text: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raw = (text or "").strip()
        toks = _tokens(raw)
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
            for a, b in schema.get("boost_pairs") or []:
                if _pair_hit(toks, a, b):
                    score += 2.2
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
