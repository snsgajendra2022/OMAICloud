"""Online response evaluation — correctness, completeness, relevance, safety, quality."""
from __future__ import annotations

import re
from typing import Any


def evaluate_response(
    question: str,
    answer: str,
    *,
    intent: str = "chat",
    required_output: str = "",
) -> dict[str, Any]:
    """Score a live reply on the five production dimensions (0–100)."""
    q = (question or "").strip()
    a = (answer or "").strip()
    q_low = q.lower()
    a_low = a.lower()
    q_toks = {t for t in re.findall(r"[a-z0-9]{3,}", q_low)} - {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "please",
    }

    overlap = sum(1 for t in q_toks if t in a_low)
    relevance = min(100.0, 35.0 + overlap * 10.0) if q_toks else 60.0
    if required_output and required_output.lower().split()[0] in a_low:
        relevance = min(100.0, relevance + 10.0)

    completeness = 40.0 if a else 0.0
    if len(a) >= 80:
        completeness += 20.0
    if a.count("\n## ") >= 2 or a.count("\n- ") >= 3:
        completeness += 20.0
    if intent in {"coding", "debug", "architecture"}:
        if any(h in a_low for h in ("architecture", "test", "deploy", "install")):
            completeness += 15.0
        if "```" in a:
            completeness += 10.0
    completeness = min(100.0, completeness)

    correctness = 55.0 if a else 0.0
    if overlap:
        correctness += min(25.0, overlap * 5.0)
    if re.search(r"\b(i don't know|cannot understand|as an ai language)\b", a_low):
        correctness -= 20.0
    correctness = max(0.0, min(100.0, correctness))

    safety = 90.0
    if re.search(r"(api[_-]?key\s*=\s*['\"]?\w{8,}|sk-[a-z0-9]{10,})", a_low):
        safety -= 50.0
    if "password" in a_low and not any(w in a_low for w in ("hash", "never", "bcrypt", "argon")):
        safety -= 15.0
    if "important:" in a_low and "secret" in a_low:
        safety = min(100.0, safety + 5.0)
    safety = max(0.0, min(100.0, safety))

    quality = 40.0 if a else 0.0
    if not re.search(r"\b(\w+)(?:\s+\1){2,}\b", a):
        quality += 15.0
    if a.count("...") < 6:
        quality += 10.0
    words = len(re.findall(r"\w+", a))
    if 20 <= words <= 2500:
        quality += 20.0
    if intent in {"greeting", "chat"} and words < 12 and words >= 3:
        quality = max(quality, 70.0)
    quality = min(100.0, quality)

    dims = {
        "correctness": round(correctness, 1),
        "completeness": round(completeness, 1),
        "relevance": round(relevance, 1),
        "safety": round(safety, 1),
        "quality": round(quality, 1),
    }
    overall = round(sum(dims.values()) / 5.0, 1)
    missing: list[str] = []
    if intent in {"coding", "debug"} and "test" not in a_low:
        missing.append("testing")
    if intent in {"coding", "architecture"} and "architecture" not in a_low and "file" not in a_low:
        missing.append("architecture_or_files")
    understood = overlap >= 1 or not q_toks
    return {
        "dimensions": dims,
        "overall": overall,
        "ok": overall >= 62.0 and safety >= 50.0,
        "understood": understood,
        "answered_actual_question": relevance >= 50.0,
        "missing": missing,
        "action": "accept" if overall >= 62.0 and not missing else "improve",
    }
