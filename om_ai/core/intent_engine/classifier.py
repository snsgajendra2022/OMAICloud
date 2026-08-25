"""Intent engine — classify / route / detect task (wraps understanding + analyzer)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentClassification:
    intent: str
    domain: str
    framework: str = ""
    task: str = ""
    agent: str = "master"
    confidence: float = 0.6
    entities: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "domain": self.domain,
            "framework": self.framework,
            "task": self.task,
            "agent": self.agent,
            "confidence": self.confidence,
            "entities": self.entities,
            "meta": self.meta,
        }


_FRAMEWORKS = [
    ("react", re.compile(r"\breact\b", re.I)),
    ("nextjs", re.compile(r"\bnext\.?js\b", re.I)),
    ("fastapi", re.compile(r"\bfastapi\b", re.I)),
    ("laravel", re.compile(r"\blaravel\b", re.I)),
    ("spring", re.compile(r"\bspring\b", re.I)),
    ("django", re.compile(r"\bdjango\b", re.I)),
]


def classify(text: str) -> IntentClassification:
    from om_ai.core.reasoning.analyzer import IntentAnalyzer
    from om_ai.understanding import understand_message

    q = (text or "").strip()
    base = IntentAnalyzer().analyze(q)
    u = understand_message(q)
    framework = ""
    for name, pat in _FRAMEWORKS:
        if pat.search(q):
            framework = name
            break
    domain = base.domain
    if framework in {"react", "nextjs"}:
        domain = "frontend"
    elif framework in {"fastapi", "django", "laravel", "spring"}:
        domain = "backend"
    agent = "coding" if base.intent in {"coding", "debug", "architecture"} else "master"
    if base.intent == "research":
        agent = "research"
    if base.intent == "business":
        agent = "business"
    return IntentClassification(
        intent=base.intent if u.confidence < 0.85 else (u.intent or base.intent),
        domain=domain,
        framework=framework,
        task=u.goal or q[:120],
        agent=agent,
        confidence=max(float(u.confidence or 0.5), 0.55),
        entities=list(base.entities),
        meta={"source": "om-intent-engine-v1", "understanding": u.intent},
    )


def detect_task(text: str) -> dict[str, Any]:
    c = classify(text)
    return {
        "task": c.task,
        "intent": c.intent,
        "domain": c.domain,
        "framework": c.framework,
        "suggested_agent": c.agent,
    }
