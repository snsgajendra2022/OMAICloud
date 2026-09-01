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

    # Prefer real dataset brain / RAG before any template
    try:
        from om_ai.brain.dataset_engine import grounded_or_none

        hit = grounded_or_none(question or "")
        if hit and len(hit) > 60:
            return hit
    except Exception:
        pass

    import os

    if os.environ.get("OM_STATIC_TEMPLATES", "0").strip() in {"1", "true", "yes", "on"}:
        from om_ai.agent.useful_reply import useful_reply_for

        useful = useful_reply_for(question, intent=intent or "chat")
        if useful:
            return useful

    qlow = (question or "").lower()
    if any(
        w in qlow
        for w in ("code", "react", "api", "login", "design", "fix", "bug", "python", "paython")
    ):
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        result = run_reasoning_pipeline(question, retrieve=True)
        sol = str(result.get("solution") or "")
        if "```" in sol:
            return sol
        return result.get("markdown") or answer

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
