"""Full reasoning pipeline used by API + CLI."""
from __future__ import annotations

from typing import Any

from om_ai.cognition.task_planner import TaskPlanner
from om_ai.cognition.technology_engine import TechnologyEngine
from om_ai.evaluation.knowledge_confidence import KnowledgeConfidenceEngine
from om_ai.knowledge.retrieval import search_knowledge
from om_ai.knowledge.ranker import KnowledgeRanker

from .analyzer import IntentAnalyzer
from .planner import PlanningEngine
from .solver import SolutionGenerator
from .verifier import VerificationEngine
from .reflection import ReflectionEngine

def _empty_technology() -> dict[str, Any]:
    return {
        "technology": None,
        "category": "unknown",
        "language": None,
        "platform": None,
        "confidence": 0,
    }

def _rank_knowledge_hits(
    question: str,
    hits: list[str],
    intent: Any,
    technology: dict[str, Any] | None = None,
) -> list[str]:
    """
    OM Knowledge Ranking Layer

    Ranks filtered knowledge before reasoning.

    Uses:
    - keyword relevance
    - domain
    - technology
    - quality
    - source trust
    """

    if not hits:
        return []


    try:

        ranker = KnowledgeRanker()


        documents = [

            {
                "text": text,

                "domain":
                    getattr(intent, "domain", "general"),

                "quality_score":
                    0.5,

                "source":
                    "knowledge_brain"

            }

            for text in hits

        ]


        ranked = ranker.rank(

            question,

            documents,

            intent=intent.to_dict()
                if hasattr(intent, "to_dict")
                else None,

            technology=technology

        )


        return [

            item.text

            for item in ranked[:5]

        ]


    except Exception:

        return hits

def _filter_knowledge_hits(question: str, hits: list[str], technology: dict[str, Any] | None = None) -> list[str]:
    if not hits:
        return []
    try:
        from om_ai.knowledge.context_filter import KnowledgeContextFilter

        raw = KnowledgeContextFilter().filter_hits(
            question,
            hits,
            technology=technology,
        )
        out: list[str] = []
        for item in raw or []:
            if isinstance(item, dict):
                text = str(item.get("text") or item.get("answer") or "").strip()
            else:
                text = str(item or "").strip()
            if text:
                out.append(text)
        return out
    except Exception:
        return hits


def _retrieve_knowledge(
    question: str,
    k: int = 4,
    *,
    intent: dict | None = None,
    technology: dict | None = None
) -> list[str]:
    hits: list[str] = []
    filters = {}
    if intent:

     domain = intent.get(
        "domain"
     )

    if domain:

        filters["domain"] = domain
    if technology:
      tech = technology.get(
        "technology"
      )
    if tech:
        filters["technology"] = tech
    try:
        from om_ai.knowledge.facts import lookup_fact

        fact = lookup_fact(question)
        if fact and fact.get("answer"):
            hits.append(str(fact["answer"]))
    except Exception:
        pass
    try:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        layer = VectorKnowledgeLayer()
        from om_ai.knowledge.retrieval import HybridRetriever

        layer = HybridRetriever()
        for row in layer.search(question,k=k,filters=filters) or []:
            if isinstance(row, dict):
                text = str(row.get("text") or row.get("chunk") or row.get("content") or "")
            else:
                text = str(getattr(row, "text", "") or row)
            text = text.strip()
            if text and text not in hits:
                hits.append(text[:400])
    except Exception:
        try:
            from om_ai.knowledge.rag import PersistentKnowledgeBase

            kb = PersistentKnowledgeBase()
            for row in kb.search(question, tenant_id="default", k=k) or []:
                text = str(getattr(row, "text", "") or "").strip()
                if text and text not in hits:
                    hits.append(text[:400])
        except Exception:
            pass
    return _filter_knowledge_hits(question, hits)


def format_reasoning_markdown(result: dict[str, Any]) -> str:
    """ChatGPT-class section layout for humans + eval contains-checks."""
    intent = result.get("intent") or {}
    plan = result.get("plan") or []
    arch = result.get("architecture") or []
    technology = result.get("technology") or {}
    evaluation = result.get("evaluation") or {}
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
        "## Technology",
        f"- Technology: {technology.get('technology')}",
        f"- Category: {technology.get('category')}",
        f"- Platform: {technology.get('platform')}",
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
        f"- Confidence: {result.get('confidence')}",
        "",
        "## Evaluation",
        f"- approved: {evaluation.get('approved')}",
        f"- score: {evaluation.get('score')}",
        *[f"- issue: {i}" for i in (evaluation.get("issues") or [])],
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
    messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from om_ai.understanding.query_kind import is_coding_task, query_kind

    kind = query_kind(question)


    hits = list(knowledge_hits or [])
    if kind == "greeting":
        hits = []
        retrieve = False
    intent = IntentAnalyzer().analyze(
        question,
        messages=messages
    )
    technology = TechnologyEngine().analyze(
        question
    )
    if retrieve and not hits:
        hits = _retrieve_knowledge(question,intent=intent.to_dict(),technology=technology)
        intent = IntentAnalyzer().analyze(
        question
    )
    if not is_coding_task(question):
        technology = {
            "technology": None,
            "category": "unknown",
            "language": None,
            "platform": None,
            "confidence": 0,
        }
    if retrieve and not hits:

        hits = _retrieve_knowledge(

            question,

            intent=intent.to_dict(),

            technology=technology

        )


    knowledge_profile = None
    try:
        from om_ai.knowledge.selector import select_knowledge

        knowledge_profile = select_knowledge(question, hits)
        if knowledge_profile.kept:
            hits = knowledge_profile.kept
    except Exception:
        knowledge_profile = None
    intent = IntentAnalyzer().analyze(question, messages=messages)
    technology = TechnologyEngine().analyze(question)
    if not is_coding_task(question):
        technology = _empty_technology()
        
    confidence_check = (
        KnowledgeConfidenceEngine()
        .evaluate(
            question,
            [
                {
                    "text": h
                }
                for h in hits
            ]
        )
    )


    if confidence_check.retry_needed:


     retry_hits = _retrieve_knowledge(

        question,

        k=8,

        intent=intent.to_dict(),

        technology=technology

    )
    if retry_hits:

        hits.extend(
            retry_hits
        )

    hits = _filter_knowledge_hits(question, hits, technology)
    hits = _rank_knowledge_hits(

    question,

    hits,

    intent,

    technology

    )
    if knowledge_profile is not None:
        knowledge_profile.kept = list(hits)
    plan = PlanningEngine().plan(intent)
    task_info = TaskPlanner().decompose(question)
    if (
        kind == "coding"
        and task_info.get("tasks")
        and task_info.get("category") not in {"", "general"}
    ):
        plan.plan = list(task_info["tasks"])
        plan.meta["task_planner"] = task_info.get("category")
    if technology.get("technology"):
        intent.meta["technology"] = technology
    solution = SolutionGenerator().solve(
        question, intent, plan, knowledge_hits=hits
    )
    knowledge_confidence = (
    KnowledgeConfidenceEngine()
        .evaluate(
            question,
            [
                {
                    "text": h
                }
                for h in hits
            ]
        )
    )
    verify = VerificationEngine().verify(intent, solution)
    reflection = ReflectionEngine().reflect(verify, domain=intent.domain)
    from om_ai.evaluation.self_checker import SelfEvaluator

    evaluation = SelfEvaluator().evaluate(
        question,
        solution.solution,
        technology,
    )
    conf = float(verify.score or 0.0)
    if knowledge_profile and knowledge_profile.kept:
        conf = min(1.0, conf + 0.05)
    if solution.meta.get("coding_kind"):
        conf = min(1.0, conf + 0.05)
    result = {
        "understanding": intent.understanding,
        "intent": intent.to_dict(),
        "technology": technology,
        "plan": plan.plan,
        "agents": plan.agents,
        "solution": solution.solution,
        "architecture": solution.architecture,
        "implementation_notes": solution.implementation_notes,
        "validation": verify.validation,
        "passed": verify.passed,
        "score": verify.score,
        "confidence": round(conf, 3),
        "critique": reflection.critique,
        "weak_areas": reflection.weak_areas,
        "training_hints": reflection.training_hints,
        "evaluation": evaluation,
        "markdown": "",
        "knowledge": knowledge_profile.to_dict() if knowledge_profile else {},
        "meta": {
            "pipeline": "om-human-like-reasoning-v1",
            "knowledge_hits": len(hits),
            "knowledge_ranking": True,
            "ranked_context_count": len(hits),
            "confidence": round(conf, 3),
            "technology": technology,
            **(solution.meta or {}),
        },
        "knowledge_confidence": {
            "score":
                knowledge_confidence.score,
            "level":
                knowledge_confidence.confidence,
            "retry_needed":
                knowledge_confidence.retry_needed,
            "reasons":
                knowledge_confidence.reasons
        },
    }
    result["markdown"] = format_reasoning_markdown(result)
    try:
        from om_ai.core.response.response_formatter import ResponseFormatter

        fmt = ResponseFormatter()
        payload = {
            "question": question,
            "intent": result.get("intent") or {},
            "technology": technology,
            "reasoning": result,
            "answer": solution.solution,
            "evaluation": evaluation,
            "plan": result.get("plan") or [],
            "architecture": result.get("architecture") or [],
            "understanding": result.get("understanding") or "",
            "tasks": task_info,
        }
        result["user_response"] = fmt.format_user_response(payload)
        result["developer_response"] = result["markdown"]
    except Exception:
        result["user_response"] = result["markdown"]
        result["developer_response"] = result["markdown"]
    result["answer"] = result.get("user_response") or result.get("markdown") or ""
    result["debug"] = {
        "understanding": result.get("understanding"),
        "intent": result.get("intent"),
        "technology": result.get("technology"),
        "plan": result.get("plan"),
        "agents": result.get("agents"),
        "knowledge": result.get("knowledge"),
        "knowledge_hits": hits,
        "evaluation": result.get("evaluation"),
        "critique": result.get("critique"),
        "score": result.get("score"),
        "confidence": result.get("confidence"),
        "markdown": result.get("markdown"),
        "tasks": task_info,
    }
    return result
