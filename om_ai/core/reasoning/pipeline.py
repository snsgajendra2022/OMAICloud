"""Full reasoning pipeline used by API + CLI."""
from __future__ import annotations

from typing import Any

from .analyzer import IntentAnalyzer
from .planner import PlanningEngine
from .solver import SolutionGenerator
from .verifier import VerificationEngine
from .reflection import ReflectionEngine


def _retrieve_knowledge(question: str, k: int = 4) -> list[str]:
    hits: list[str] = []
    try:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        layer = VectorKnowledgeLayer()
        for row in layer.search(question, k=k) or []:
            if isinstance(row, dict):
                text = str(row.get("text") or row.get("chunk") or row.get("content") or "")
            else:
                text = str(getattr(row, "text", "") or row)
            text = text.strip()
            if text:
                hits.append(text[:400])
    except Exception:
        try:
            from om_ai.knowledge.rag import PersistentKnowledgeBase

            kb = PersistentKnowledgeBase()
            for row in kb.search(question, tenant_id="default", k=k) or []:
                text = str(getattr(row, "text", "") or "").strip()
                if text:
                    hits.append(text[:400])
        except Exception:
            pass
    return hits


def format_reasoning_markdown(result: dict[str, Any]) -> str:
    """ChatGPT-class section layout for humans + eval contains-checks."""
    intent = result.get("intent") or {}
    plan = result.get("plan") or []
    arch = result.get("architecture") or []
    arch_lines = [f"- {a}" for a in arch] if arch else ["- (see solution)"]
    lines = [
        "## Understanding",
        str(result.get("understanding") or intent.get("understanding") or ""),
        "",
        "## Analysis",
        f"- Intent: `{intent.get('intent', 'general')}`",
        f"- Domain: `{intent.get('domain', 'general')}`",
        f"- Agents: {', '.join(result.get('agents') or []) or 'master'}",
        "",
        "## Architecture",
        *arch_lines,
        "",
        "## Plan",
        *[f"{i+1}. {s}" for i, s in enumerate(plan)],
        "",
        "## Implementation",
        str(result.get("solution") or ""),
        "",
        "## Validation",
        *[f"- {v}" for v in (result.get("validation") or [])],
        f"- Passed: {result.get('passed')}",
        f"- Score: {result.get('score')}",
        "",
        "## Self-critique",
        *[f"- {c}" for c in (result.get("critique") or [])],
    ]
    weak = result.get("weak_areas") or []
    if weak:
        lines += ["", "## Weak areas", *[f"- {w}" for w in weak]]
    return "\n".join(lines).strip() + "\n"


def run_reasoning_pipeline(
    question: str,
    *,
    knowledge_hits: list[str] | None = None,
    retrieve: bool = True,
) -> dict[str, Any]:
    hits = list(knowledge_hits or [])
    if retrieve and not hits:
        hits = _retrieve_knowledge(question)
    intent = IntentAnalyzer().analyze(question)
    plan = PlanningEngine().plan(intent)
    solution = SolutionGenerator().solve(
        question, intent, plan, knowledge_hits=hits
    )
    verify = VerificationEngine().verify(intent, solution)
    reflection = ReflectionEngine().reflect(verify, domain=intent.domain)
    result = {
        "understanding": intent.understanding,
        "intent": intent.to_dict(),
        "plan": plan.plan,
        "agents": plan.agents,
        "solution": solution.solution,
        "architecture": solution.architecture,
        "implementation_notes": solution.implementation_notes,
        "validation": verify.validation,
        "passed": verify.passed,
        "score": verify.score,
        "critique": reflection.critique,
        "weak_areas": reflection.weak_areas,
        "training_hints": reflection.training_hints,
        "markdown": "",
        "meta": {
            "pipeline": "om-foundation-reasoning-v2",
            "knowledge_hits": len(hits),
            "solver": (solution.meta or {}).get("template"),
        },
    }
    result["markdown"] = format_reasoning_markdown(result)
    return result
