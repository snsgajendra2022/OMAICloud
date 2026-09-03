"""Deep understanding — semantic-style feature extraction (regex = helper signal only)."""
from __future__ import annotations

import re
from typing import Any


# Soft signal banks — scores accumulate; no single regex decides the answer.
_ACTION_SIGNALS: list[tuple[str, list[str]]] = [
    ("generate", ["create", "make", "generate", "write", "build", "draft", "compose"]),
    ("explain", ["explain", "what is", "what's", "describe", "how does", "tell me about"]),
    ("debug", ["debug", "fix", "error", "bug", "broken", "not working", "traceback"]),
    ("research", ["research", "study", "investigate", "paper", "sources"]),
    ("plan", ["plan", "roadmap", "steps", "how to start", "strategy"]),
    ("compare", ["compare", "vs", "versus", "difference", "better"]),
    ("summarize", ["summarize", "summary", "tldr", "brief"]),
    ("analyze", ["analyze", "analysis", "evaluate", "assess"]),
    ("calculate", ["calculate", "compute", "how much", "math"]),
    ("recommend", ["recommend", "suggest", "playlist", "ideas", "recommend me"]),
    ("chat", ["hello", "hi", "hey", "thanks", "thank you", "namaste"]),
]

_DOMAIN_SIGNALS: list[tuple[str, list[str]]] = [
    ("software", ["code", "react", "python", "api", "app", "laravel", "git", "prompt", "cursor", "javascript", "typescript", "debug"]),
    ("ai", ["ai", "llm", "model", "prompt", "embedding", "agent", "om ai"]),
    ("music", ["music", "playlist", "song", "spotify", "lo-fi", "beats"]),
    ("business", ["business", "revenue", "sales", "market", "restaurant", "finance", "kpi"]),
    ("science", ["quantum", "physics", "biology", "chemistry", "molecule", "computing", "relativity", "neuron"]),
    ("time", ["date", "today", "time", "clock", "day"]),
    ("writing", ["email", "letter", "essay", "blog", "copy"]),
    ("data", ["dataset", "csv", "dataframe", "sql", "schema"]),
    ("architecture", ["architecture", "system design", "diagram", "microservice"]),
]

_COMPLEXITY_HEAVY = re.compile(
    r"\b(architecture|distributed|production|enterprise|full.?stack|multi.?agent|end.?to.?end)\b",
    re.I,
)


def _score_banks(text: str, banks: list[tuple[str, list[str]]]) -> dict[str, float]:
    low = (text or "").lower()
    scores: dict[str, float] = {}
    tokens = set(re.findall(r"[a-z0-9']+", low))
    for label, words in banks:
        score = 0.0
        for w in words:
            if " " in w:
                if w in low:
                    score += 1.5
            elif w in tokens or w in low:
                score += 1.0
        if score:
            scores[label] = score
    return scores


def _best(scores: dict[str, float], default: str) -> tuple[str, float]:
    if not scores:
        return default, 0.0
    label = max(scores, key=scores.get)
    return label, float(scores[label])


class UnderstandingEngine:
    """Infer intent / goal / domain / complexity without hard category locks."""

    def understand(self, text: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        q = (text or "").strip()
        ctx = context or {}
        action_scores = _score_banks(q, _ACTION_SIGNALS)
        domain_scores = _score_banks(q, _DOMAIN_SIGNALS)

        # Context soft boosts (previous project / prefs)
        proj = str(ctx.get("project") or ctx.get("project_hint") or "").lower()
        if proj:
            if any(k in proj for k in ("om", "ai", "react", "code", "app")):
                domain_scores["software"] = domain_scores.get("software", 0) + 0.8
                domain_scores["ai"] = domain_scores.get("ai", 0) + 0.5
        recent = " ".join(str(x) for x in (ctx.get("recent_tasks") or [])[:5]).lower()
        if "prompt" in recent and "prompt" in q.lower():
            action_scores["generate"] = action_scores.get("generate", 0) + 1.0
            domain_scores["ai"] = domain_scores.get("ai", 0) + 0.8

        action, action_score = _best(action_scores, "explain" if "?" in q else "chat")
        domain, domain_score = _best(domain_scores, "general")

        # Temporal questions: prefer datetime intent even when phrasing is terse.
        low = q.lower()
        if domain == "time" or re.search(r"\b(today'?s?\s+date|current\s+date|what\s+date|what\s+time)\b", low):
            domain = "time"
            action = "calculate"
            intent_force = "datetime"
        else:
            intent_force = None

        # Goal paraphrase (not a template answer)
        goal = self._goal(q, action, domain)
        complexity = "high" if _COMPLEXITY_HEAVY.search(q) or len(q.split()) > 40 else (
            "medium" if len(q.split()) > 8 or action in {"generate", "debug", "plan", "analyze"} else "low"
        )

        intent = intent_force or self._intent_label(action, domain, q)
        required_action = action if action != "chat" else ("answer" if len(q.split()) > 2 else "greet")

        confidence = min(0.95, 0.35 + 0.12 * max(action_score, domain_score))
        return {
            "intent": intent,
            "goal": goal,
            "domain": domain,
            "complexity": complexity,
            "required_action": required_action,
            "action_scores": action_scores,
            "domain_scores": domain_scores,
            "confidence": round(confidence, 3),
            "raw": q,
            "signals_only": True,  # helper signals — not final answer authority
        }

    def _intent_label(self, action: str, domain: str, q: str) -> str:
        low = q.lower()
        if action == "generate" and "prompt" in low:
            return "create_prompt"
        if action == "chat" and len(q.split()) <= 4:
            return "chat"
        if domain == "time" and action in {"explain", "chat", "calculate"}:
            return "datetime"
        if action == "recommend" and domain == "music":
            return "recommend"
        mapping = {
            "generate": "create",
            "explain": "question",
            "debug": "debug",
            "research": "research",
            "plan": "plan",
            "compare": "compare",
            "summarize": "summarize",
            "analyze": "analyze",
            "calculate": "calculate",
            "recommend": "recommend",
            "chat": "chat",
        }
        return mapping.get(action, action or "question")

    def _goal(self, q: str, action: str, domain: str) -> str:
        if not q:
            return "empty request"
        verbs = {
            "generate": "produce",
            "explain": "explain",
            "debug": "fix",
            "research": "research",
            "plan": "plan",
            "recommend": "recommend",
            "analyze": "analyze",
            "summarize": "summarize",
            "compare": "compare",
            "calculate": "compute",
            "chat": "converse about",
        }
        return f"{verbs.get(action, 'help with')} {domain} request: {q[:120]}"
