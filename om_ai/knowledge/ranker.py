"""Knowledge domain catalog + source ranking for retrieval."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

DOMAINS = (
    "programming",
    "engineering",
    "science",
    "mathematics",
    "business",
    "finance",
    "education",
    "medicine",
    "research",
    "history",
    "design",
    "artificial_intelligence",
)

_DOMAIN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("programming", re.compile(r"\b(code|python|javascript|react|api|sql|docker|git)\b", re.I)),
    ("artificial_intelligence", re.compile(r"\b(ai|llm|model|transformer|rag|embedding)\b", re.I)),
    ("engineering", re.compile(r"\b(architect|system|scale|latency|infra)\b", re.I)),
    ("mathematics", re.compile(r"\b(math|algebra|calculus|proof|equation)\b", re.I)),
    ("science", re.compile(r"\b(physics|chemistry|biology|experiment)\b", re.I)),
    ("business", re.compile(r"\b(market|revenue|strategy|ops|kpi)\b", re.I)),
    ("finance", re.compile(r"\b(finance|stock|accounting|invoice|tax)\b", re.I)),
    ("education", re.compile(r"\b(course|lesson|curriculum|student|teach)\b", re.I)),
    ("medicine", re.compile(r"\b(clinical|patient|diagnosis|drug)\b", re.I)),
    ("design", re.compile(r"\b(ui|ux|layout|typography|figma)\b", re.I)),
    ("history", re.compile(r"\b(history|century|ancient|war of)\b", re.I)),
    ("research", re.compile(r"\b(paper|survey|citation|hypothesis)\b", re.I)),
]


@dataclass
class RankedSource:
    text: str
    score: float
    domain: str = "general"
    reason: str = ""


@dataclass
class RankResult:
    domain: str
    ranked: list[RankedSource] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "ranked": [{"text": r.text[:400], "score": r.score, "reason": r.reason} for r in self.ranked],
            "dropped": self.dropped,
        }


def detect_domain(question: str) -> str:
    for name, pat in _DOMAIN_PATTERNS:
        if pat.search(question or ""):
            return name
    return "general"


def rank_sources(question: str, snippets: list[str] | None = None) -> RankResult:
    domain = detect_domain(question)
    q_toks = set(re.findall(r"[a-z0-9]{3,}", (question or "").lower()))
    howto = bool(re.search(r"\b(how to|create|implement|build)\b", question or "", re.I))
    ranked: list[RankedSource] = []
    dropped: list[str] = []
    for raw in snippets or []:
        text = (raw or "").strip()
        if not text:
            continue
        low = text.lower()
        if howto and re.search(r"\b(history of|invented by|founded in)\b", low):
            dropped.append(text[:200])
            continue
        overlap = sum(1 for t in q_toks if t in low)
        score = overlap / max(1, min(12, len(q_toks)))
        if domain != "general" and domain.replace("_", " ") in low:
            score += 0.15
        ranked.append(RankedSource(text=text, score=round(score, 3), domain=domain, reason="token_overlap"))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return RankResult(domain=domain, ranked=ranked[:8], dropped=dropped[:6])
