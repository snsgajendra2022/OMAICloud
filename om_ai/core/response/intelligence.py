"""Response Quality Engine — structure, grammar heuristics, solve-check, polish."""
from __future__ import annotations

import re
from typing import Any

from om_ai.core.response.quality import check_quality
from om_ai.improvement.evaluator import evaluate_answer


def analyze_response(question: str, answer: str) -> dict[str, Any]:
    gate = check_quality(answer, user_ask=question)
    scores = evaluate_answer(question, answer)
    issues: list[str] = []
    if not gate["ok"]:
        issues.append(f"quality_gate:{gate['reason']}")
    if scores["overall"] < 70:
        issues.append("low_overall_score")
    # crude grammar / garble markers
    if re.search(r"\b(\w+)(?:\s+\1){2,}\b", answer or "", re.I):
        issues.append("word_loop")
    if answer and answer.count("...") > 5:
        issues.append("ellipsis_spam")
    understandable = gate["ok"] and "garbled" not in issues and scores["scores"].get("clarity", 0) >= 50
    return {
        "understandable": understandable,
        "grammar_ok": "word_loop" not in issues,
        "structure_ok": scores["scores"].get("structure", 0) >= 60,
        "solves_request": scores["scores"].get("task_fit", 0) >= 65,
        "issues": issues,
        "gate": gate,
        "scores": scores,
        "action": "accept" if understandable and scores["ok"] else "repair",
    }


def repair_response(question: str, answer: str, *, intent: str = "chat") -> str:
    analysis = analyze_response(question, answer)
    if analysis["action"] == "accept":
        return answer
    # Prefer reasoning pipeline for coding/design; else compose_fallback
    qlow = (question or "").lower()
    if any(w in qlow for w in ("code", "react", "api", "login", "design", "fix", "bug")):
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        return run_reasoning_pipeline(question, retrieve=True).get("markdown") or answer
    from om_ai.agent.verifier import compose_fallback

    return compose_fallback(intent=intent or "chat", user_text=question)


def ensure_intelligent_response(question: str, answer: str, *, intent: str = "chat") -> dict[str, Any]:
    analysis = analyze_response(question, answer)
    final = answer if analysis["action"] == "accept" else repair_response(question, answer, intent=intent)
    # Feed improvement engine when repaired or weak
    improve = None
    if analysis["action"] == "repair" or not analysis["scores"].get("ok", True):
        try:
            from om_ai.improvement import improve_from_exchange

            improve = improve_from_exchange(question, answer, bump=True)
        except Exception as exc:
            improve = {"error": str(exc)}
    return {
        "final": final,
        "repaired": final != answer,
        "analysis": analysis,
        "improvement": improve,
    }
