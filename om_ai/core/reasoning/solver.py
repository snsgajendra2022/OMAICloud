"""Solution generator — dataset + RAG + model first. No static code by default."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from .analyzer import IntentResult
from .planner import PlanResult


def _intent_engine():
    from om_ai.cognition.intent_engine import IntentEngine

    return IntentEngine()


def _relevance_checker():
    from om_ai.rag.relevance_checker import RelevanceChecker

    return RelevanceChecker(min_score=0.65)

def _static_templates_enabled() -> bool:
    return os.environ.get("OM_STATIC_TEMPLATES", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _model_solver_enabled() -> bool:
    return os.environ.get("OM_SOLVER_USE_MODEL", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


@dataclass
class SolutionResult:
    solution: str
    architecture: list[str] = field(default_factory=list)
    implementation_notes: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "solution": self.solution,
            "architecture": self.architecture,
            "implementation_notes": self.implementation_notes,
            "meta": self.meta,
        }


def _extract_code_block(text: str) -> str | None:
    if not text or "```" not in text:
        return None
    return text.strip()


def _solution_from_dataset(
    question: str,
) -> tuple[str, list[str], list[str], dict[str, Any]] | None:
    """
    Retrieve dataset knowledge only when it is relevant to the user's
    actual intent. Dataset text is treated as knowledge, not blindly
    trusted as the final answer.
    """
    try:
        from om_ai.brain.dataset_engine import retrieve_answer

        # 1. Understand the user's request first.
        detected_intent = _intent_engine().analyze(question)

        # 2. Retrieve candidate knowledge.
        hit = retrieve_answer(question, min_score=0.65)

        if not hit:
            return None

        # 3. Validate retrieved knowledge against intent/domain/score.
        decision = _relevance_checker().check(
            question,
            hit,
            detected_intent,
        )

        if not decision.accepted:
            return None

        answer = str(hit.get("answer") or "").strip()

        if len(answer) < 60:
            return None

        arch = [
            "Intent-aware OM dataset retrieval",
            "Retrieved knowledge passed relevance validation",
        ]

        notes = [
            f"source={hit.get('source')}",
            f"domain={hit.get('domain')}",
            f"score={hit.get('score')}",
            f"intent_domain={detected_intent.get('domain')}",
            f"relevance={decision.reason}",
        ]

        meta = {
            "template": None,
            "source": "dataset_brain",
            "dataset_id": hit.get("id"),
            "score": hit.get("score"),
            "intent": detected_intent,
            "relevance": {
                "accepted": decision.accepted,
                "reason": decision.reason,
                "confidence": decision.confidence,
            },
        }

        body = answer.strip() + "\n"

        return body, arch, notes, meta

    except Exception:
        return None


def intent_understanding_stub(question: str) -> str:
    return f"User wants help with: {question.strip()[:240]}"


def _solution_from_knowledge_hits(
    question: str,
    hits: list[str],
    intent: IntentResult,
    plan: PlanResult,
) -> tuple[str, list[str], list[str], dict[str, Any]] | None:
    if not hits:
        return None
    # Prefer a hit that already contains runnable code
    for h in hits:
        if "```" in h and len(h) > 80:
            body = h.strip() + "\n"
            return (
                body,
                ["Grounded in retrieved knowledge", "Adapt paths to your project"],
                [f"Intent={intent.intent}", f"Agents: {', '.join(plan.agents)}"],
                {"template": None, "source": "knowledge_hits", "has_code": True},
            )
    snippets = "\n\n".join(h.strip() for h in hits[:4] if h.strip())
    body = snippets + "\n"
    return (
        body,
        ["Use retrieved knowledge", "Minimal change → verify → document"],
        [f"Retrieved {len(hits)} snippets"],
        {"template": None, "source": "knowledge_hits"},
    )


def _solution_from_model(question: str, intent: IntentResult) -> tuple[str, list[str], list[str], dict[str, Any]] | None:
    """Optional: ask OM-1.0 to generate code (real model, not canned template)."""
    if not _model_solver_enabled():
        return None
    if intent.intent not in {"coding", "debug", "architecture"} and intent.domain != "software":
        return None
    try:
        from om_ai.runtime.chat_backend import chat_complete

        system = (
            "You are OM coding intelligence. Generate production-quality code for the user ask. "
            "Include fenced code blocks. Match their stack if stated. No filler."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question.strip()},
        ]
        text, _info = chat_complete(messages, max_new_tokens=384, temperature=0.35)
        text = (text or "").strip()
        if not text or len(text) < 40:
            return None
        from om_ai.runtime.chat_orchestrator import is_low_quality_reply

        if is_low_quality_reply(text):
            return None
        body = text.strip() + "\n"
        has_code = "```" in text
        return (
            body,
            ["Model-generated implementation", "Review security and tests before merge"],
            ["source=native_model"],
            {"template": None, "source": "native_model", "has_code": has_code},
        )
    except Exception:
        return None


def _coding_blueprint(question: str, intent: IntentResult) -> Any | None:
    try:
        from om_ai.core.reasoning.coding_intelligence import build_coding_blueprint

        canonical = ""
        meta_u = (intent.meta or {}).get("understanding") or {}
        if isinstance(meta_u, dict):
            canonical = str(meta_u.get("canonical") or meta_u.get("goal") or "")
        return build_coding_blueprint(question, canonical=canonical or intent.understanding)
    except Exception:
        return None


def _solution_from_plan_only(
    question: str,
    intent: IntentResult,
    plan: PlanResult,
) -> tuple[str, list[str], list[str], dict[str, Any]]:
    bp = None
    if intent.intent in {"coding", "debug", "architecture", "performance"}:
        bp = _coding_blueprint(question, intent)

    extra = ""
    arch = ["Load dataset brain", "Retrieve similar solutions", "Implement minimal fix", "Verify"]
    notes = [f"Intent={intent.intent}", f"Agents: {', '.join(plan.agents)}"]
    meta: dict[str, Any] = {"template": None, "source": "plan_only"}

    if intent.intent == "performance":
        causes = list((plan.meta or {}).get("causes") or [])
        extra = (
            "## Possible causes\n"
            + "\n".join(f"- {c}" for c in (causes or [
                "Database query",
                "Images",
                "JS bundle",
                "Server resources",
                "API latency",
                "Cache",
            ]))
            + "\n\nDo not start with “increase server”. Check evidence first.\n"
        )
        meta["source"] = "diagnostic"

    if bp:
        extra = (extra + "\n\n" + bp.markdown).strip() + "\n"
        arch = list(bp.architecture) or arch
        notes = list(bp.notes) + notes
        meta["coding_kind"] = (bp.meta or {}).get("kind")

    body = extra.strip()
    if not body:
        try:
            from om_ai.knowledge.facts import lookup_fact

            fact = lookup_fact(question)
            if fact and fact.get("answer"):
                body = str(fact["answer"]).strip()
        except Exception:
            body = ""
    if not body:
        body = (
            f"{question.strip()}\n\n")
    notes = [f"Intent={intent.intent}"]
    return body, arch, notes, meta


# Legacy static templates — ONLY when OM_STATIC_TEMPLATES=1 (dev/demo)
def _react_login_solution_static(question: str) -> tuple[str, list[str], list[str]]:
    arch = ["src/Login.jsx", "src/Login.css", "Auth API client"]
    notes = ["OM_STATIC_TEMPLATES=1 — demo template only"]
    code = "```jsx\n// static demo — disable OM_STATIC_TEMPLATES for real AI\nexport default function Login() { return null; }\n```"
    solution = f"**Ask:** {question[:300]}\n\n## Implementation (static demo)\n{code}\n"
    return solution, arch, notes


def _school_management_solution_static(question: str) -> tuple[str, list[str], list[str]]:
    arch = ["Students", "Teachers", "Classes", "Attendance", "Grades"]
    notes = ["OM_STATIC_TEMPLATES=1 — demo template only"]
    solution = f"**Ask:** {question[:300]}\n\n## Architecture (static demo)\n- Multi-role SMS\n"
    return solution, arch, notes


class SolutionGenerator:
    def solve(
        self,
        question: str,
        intent: IntentResult,
        plan: PlanResult,
        *,
        knowledge_hits: list[str] | None = None,
    ) -> SolutionResult:
        q = (question or "").strip()
        hits = list(knowledge_hits or [])
        meta: dict[str, Any] = {"solver": "om-solver-v3"}
        tech_name = str(((intent.meta or {}).get("technology") or {}).get("technology") or "").lower()
        blob = " ".join(hits).lower()
        hits_fit = True
        if intent.intent in {"coding", "debug", "architecture"} and tech_name:
            hits_fit = tech_name in blob or "```" in blob

        # 1) Real corpus retrieval (not canned code)
        ds = _solution_from_dataset(q)
        if ds:
            solution, arch, notes, m = ds
            meta.update(m)
            return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)

        # 2) RAG / knowledge hits passed into pipeline
        kh = _solution_from_knowledge_hits(q, hits, intent, plan) if hits_fit else None
        if kh and ("```" in kh[0] or (len(hits) >= 2 and hits_fit and intent.intent not in {"coding", "debug", "architecture"})):
            solution, arch, notes, m = kh
            meta.update(m)
            return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)

        # 3) Native model generation (real weights, not template)
        mg = _solution_from_model(q, intent)
        if mg:
            solution, arch, notes, m = mg
            meta.update(m)
            return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)

        # 4) Legacy static — explicit opt-in only
        if _static_templates_enabled():
            qlow = q.lower()
            if re.search(r"\breact\b", qlow) and re.search(r"\b(login|sign\s*in|auth|signup)\b", qlow):
                solution, arch, notes = _react_login_solution_static(q)
                meta.update({"template": "react_login_static", "source": "static_demo"})
                return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)
            if re.search(r"\bschool\b", qlow) and re.search(r"\b(management|sms|erp)\b", qlow):
                solution, arch, notes = _school_management_solution_static(q)
                meta.update({"template": "school_management_static", "source": "static_demo"})
                return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)

        # 5) Knowledge hits without code, or general intent
        if kh and hits_fit:
            solution, arch, notes, m = kh
            meta.update(m)
            return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)

        solution, arch, notes, m = _solution_from_plan_only(q, intent, plan)
        meta.update(m)
        return SolutionResult(solution=solution, architecture=arch, implementation_notes=notes, meta=meta)
