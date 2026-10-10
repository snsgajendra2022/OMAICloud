"""Score an OM answer for structure, clarity, security, and task fit."""
from __future__ import annotations

import re
from typing import Any


def evaluate_answer(question: str, answer: str) -> dict[str, Any]:
    q = (question or "").strip()
    a = (answer or "").strip()
    scores: dict[str, float] = {}

    # Structure
    headers = len(re.findall(r"^#{1,3}\s+\w+", a, re.M))
    scores["structure"] = min(100.0, 40.0 + headers * 15.0) if a else 0.0

    # Clarity / length sanity
    words = len(re.findall(r"\w+", a))
    is_short_greet = bool(
        re.match(r"^(hi|hey|hello|namaste|good (morning|evening|afternoon)|i'?m om|i am om)\b", a, re.I)
    ) or bool(
        re.search(r"\b(hi|hello|hey|greetings|namaste|good morning|good evening|good afternoon|how are you)\b", q, re.I)
    )
    if is_short_greet and words <= 15 and a:
        scores["clarity"] = 90.0
        scores["structure"] = 85.0
        scores["task_fit"] = 90.0
    elif words < 8:
        scores["clarity"] = 25.0
    elif words > 4000:
        scores["clarity"] = 55.0
    else:
        scores["clarity"] = min(100.0, 50.0 + words / 10.0)

    # Security heuristics
    low = a.lower()
    sec = 80.0
    if "password" in low and "hash" not in low and "httpOnly" not in low and "validate" not in low:
        sec -= 15.0
    if any(x in low for x in ("api_key =", "sk-", "password = \"", ".env")):
        sec -= 40.0
    if "secret" in low and "never" in low:
        sec = min(100.0, sec + 10.0)
    scores["security"] = max(0.0, min(100.0, sec))

    # Task fit
    q_tokens = set(re.findall(r"[a-z0-9]+", q.lower())) - {"a", "the", "to", "and", "for", "of"}
    hit = sum(1 for t in q_tokens if t in low)
    scores["task_fit"] = min(100.0, 30.0 + hit * 12.0) if q_tokens else 50.0

    # Code presence when coding ask
    coding = bool(re.search(r"\b(code|react|api|fastapi|bug|login|jsx)\b", q, re.I))
    if coding:
        scores["code_quality"] = 85.0 if ("```" in a or "function" in low or "def " in a) else 40.0
    else:
        scores["code_quality"] = 70.0

    overall = sum(scores.values()) / max(1, len(scores))
    return {
        "question": q[:300],
        "scores": {k: round(v, 1) for k, v in scores.items()},
        "overall": round(overall, 1),
        "ok": overall >= 70.0,
    }
