"""OM Absolute Intelligence — Cognitive Operating System facade.

Observe → Understand → Remember → Research → Think → Agents →
Verify → Speak → Learn → (optional hardware)

Not: Prompt → LLM → Answer
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from om_ai.operating_intelligence.embodiment import electronics, robotics, sensors, twin


@dataclass
class CycleResult:
    goal: str
    observed: dict[str, Any] = field(default_factory=dict)
    understood: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    knowledge: dict[str, Any] = field(default_factory=dict)
    cognition: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)
    plan: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    verification: dict[str, Any] = field(default_factory=dict)
    growth: dict[str, Any] = field(default_factory=dict)
    perception: dict[str, Any] = field(default_factory=dict)
    neural: dict[str, Any] = field(default_factory=dict)
    response: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def capability_status() -> dict[str, Any]:
    from om_ai.identity import identity_card
    from om_ai.operating_intelligence import perception_bridge, neural_simulation

    return {
        "system": "OM (Operating Mind) — Genesis Intelligence Architecture",
        "principle": "Cognitive OS over foundation models — not prompt→LLM→answer",
        "cycle": [
            "observe",
            "understand",
            "remember",
            "research",
            "think",
            "agents",
            "verify",
            "respond",
            "learn",
            "neural_adapt",
        ],
        "layers": {
            "cognitive_pipeline": "live",
            "conversation_engine": "live",
            "memory_brain": "live",
            "knowledge_brain": "live",
            "reasoning_core": "live",
            "agent_civilization": "partial",
            "self_improvement": "live",
            "neural_simulation": "live",
            "voice_vision": perception_bridge.status(),
            "hardware": {
                "electronics": electronics.status(),
                "sensors": sensors.status(),
                "robotics": robotics.status(),
                "digital_twin": twin.status(),
            },
            "foundation_models": "partial (OM-1.0 local; OM-7/70B future weights)",
        },
        "capabilities": {
            "memory": "exists",
            "knowledge": "exists",
            "reasoning": "exists",
            "understanding": "exists",
            "coding": "exists",
            "agents": "partial",
            "evaluation": "exists",
            "electronics_iot": "stub",
            "robotics": "stub",
            "native_model": "partial",
        },
        "honesty": (
            "OM amplifies human+machine strengths (memory, retrieval, automation). "
            "It does not claim biological superintelligence or 100× all humans. "
            "Larger trained weights + licensed data remain the generative leap."
        ),
        "operating_rules": [
            "Understand before answering",
            "Detect intent",
            "Use memory when available",
            "Use knowledge sources",
            "Reason step-by-step internally",
            "Verify answers",
            "Improve from feedback",
            "Communicate naturally",
            "Match user's language",
            "Never pretend capabilities that do not exist",
        ],
        "identity": identity_card(),
    }


class OperatingIntelligence:
    def run(
        self,
        goal: str,
        *,
        context: dict[str, Any] | None = None,
        dry_run: bool = True,
    ) -> CycleResult:
        return run_cycle(goal, context=context, dry_run=dry_run)


def run_cycle(
    goal: str,
    *,
    context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> CycleResult:
    """Full Absolute Intelligence digital cycle (hardware gated)."""
    from om_ai.conversation_engine import classify_and_plan, control_response_style
    from om_ai.operating_intelligence import (
        agent_bridge,
        cognition_bridge,
        growth_bridge,
        knowledge_bridge,
        memory_bridge,
        neural_simulation,
        perception_bridge,
    )
    from om_ai.agent.verifier import verify_reply
    from om_ai.response_engine import format_assistant_reply

    ctx = context or {}
    goal = (goal or "").strip()
    result = CycleResult(goal=goal)
    tenant = str(ctx.get("tenant_id") or os.environ.get("OM_AI_TENANT") or "default")
    user_id = str(ctx.get("actor") or ctx.get("user_id") or "")
    project_id = ctx.get("project_id")

    # 1 Observe
    result.observed = {
        "goal": goal,
        "context_keys": sorted(ctx.keys()),
        "dry_run": dry_run,
        "message_count": len(ctx.get("messages") or []),
    }

    # 2 Understand (cognitive pipeline + conversation engine)
    msgs = list(ctx.get("messages") or [])
    mem_snips: list[str] = []
    for key in ("user", "project", "conversation"):
        for s in (ctx.get("memory") or {}).get(key) or []:
            if isinstance(s, str) and s.strip():
                mem_snips.append(s.strip()[:160])
    state = classify_and_plan(
        goal,
        messages=msgs,
        project_instructions=str(ctx.get("project_instructions") or ""),
        memory_snippets=mem_snips[:5] or None,
    )
    style = control_response_style(state)
    result.understood = {**state.to_dict(), "style": style}
    intent = state.intent
    cog = (state.meta or {}).get("cognitive") or {}
    resolved_goal = str(cog.get("goal") or state.goal or goal)
    if resolved_goal and resolved_goal != goal:
        goal = resolved_goal
        result.goal = goal

    # 3 Remember
    result.memory = memory_bridge.recall_all(
        goal, tenant_id=tenant, user_id=user_id, project_id=project_id, k=5
    )

    # 4 Research (knowledge brain)
    result.knowledge = knowledge_bridge.research(goal, tenant_id=tenant, k=6)

    # 5 Think (reasoning core)
    hits = list(result.knowledge.get("snippets") or [])[:4]
    result.cognition = cognition_bridge.think(goal, knowledge_hits=hits, messages=msgs)
    result.plan = list(state.plan or []) or list(result.cognition.get("plan") or [])

    # 6 Agent civilization
    agents = agent_bridge.select_agents(intent, goal)
    result.agents = agent_bridge.run_agents(
        goal, intent=intent, agents=agents, snippets=hits
    )

    # 7 Execute digital (hardware optional)
    actions: list[dict[str, Any]] = [
        {"type": "memory_recall", "hits": sum(len(v) for v in result.memory.values() if isinstance(v, list))},
        {"type": "knowledge", "source": result.knowledge.get("source"), "count": result.knowledge.get("count")},
        {"type": "agents", "names": agents},
    ]
    if ctx.get("allow_hardware") and not dry_run:
        actions.append(
            {
                "type": "hardware",
                "status": "stub_gated",
                "detail": electronics.command({"op": "status"}, dry_run=True),
            }
        )
    result.actions = actions

    # 8 Compose response — prefer grounded knowledge / cognition / agents
    draft = _compose_absolute_response(goal, state, result)

    # Final quality gate (Genesis identity)
    from om_ai.identity import CORE_PIPELINE, quality_gate, identity_card

    gate = quality_gate(goal, draft, intent=intent)
    if not gate.get("ok"):
        # One improve pass via growth + compose_fallback / cognition
        try:
            from om_ai.agent.verifier import compose_fallback

            alt = compose_fallback(intent=intent, user_text=goal)
            gate2 = quality_gate(goal, alt, intent=intent)
            if gate2.get("ok") or len(alt) > len(draft):
                draft = alt
                gate = gate2
        except Exception:
            pass
        if intent == "coding" and "```" not in draft:
            try:
                from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

                md = (run_reasoning_pipeline(goal, retrieve=True).get("markdown") or "").strip()
                if "```" in md:
                    draft = md
                    gate = quality_gate(goal, draft, intent=intent)
            except Exception:
                pass

    reason = verify_reply(draft, intent=intent)
    result.verification = {
        "ok": not reason and bool(gate.get("ok")),
        "reason": reason or "",
        "quality_gate": gate,
        "pipeline": CORE_PIPELINE,
    }
    result.response = format_assistant_reply(draft, intent=intent, enhance=True)
    try:
        from om_ai.cognitive import CognitiveState, polish_reply

        cog_raw = (state.meta or {}).get("cognitive") or {}
        if cog_raw:
            cog = CognitiveState(**{k: v for k, v in cog_raw.items() if k in CognitiveState.__dataclass_fields__})
            result.response = polish_reply(cog, result.response)
    except Exception:
        pass

    try:
        from om_ai.evaluation.online import evaluate_response

        eval_report = evaluate_response(
            goal,
            result.response,
            intent=intent,
            required_output=str((state.meta or {}).get("cognitive", {}).get("goal") or ""),
        )
        result.verification["evaluation"] = eval_report
        if eval_report.get("action") == "improve" and intent == "coding":
            extra = str((result.agents or {}).get("markdown") or "")
            if extra and extra not in result.response:
                result.response = (result.response.rstrip() + "\n\n" + extra).strip()
                result.verification["evaluation"] = evaluate_response(
                    goal, result.response, intent=intent
                )
    except Exception:
        pass

    try:
        from om_ai.core.response.response_formatter import ResponseFormatter, response_mode

        fmt = ResponseFormatter()
        payload = {
            "question": goal,
            "intent": {"intent": intent},
            "answer": result.response,
            "reasoning": result.cognition or {},
            "technology": (result.cognition or {}).get("technology") or {},
            "plan": result.plan or [],
            "evaluation": (result.verification or {}).get("evaluation") or {},
        }
        if response_mode() != "developer":
            result.response = fmt.format_user_response(payload)
        result.meta["developer_response"] = fmt.format_developer_response(payload)
    except Exception:
        pass

    try:
        from om_ai.memory.session import record_turn

        result.meta["memory_write"] = record_turn(
            str(result.observed.get("goal") or goal),
            tenant_id=tenant,
            user_id=user_id,
            project_id=str(project_id) if project_id else None,
            goal=goal,
            stack=list(state.technology or []),
        )
    except Exception:
        pass

    # 9 Self-improvement
    if os.environ.get("OM_ABSOLUTE_LEARN", "1").strip() not in {"0", "false", "off"}:
        result.growth = growth_bridge.improve(goal, result.response)
    else:
        result.growth = {"skipped": True}

    # 10 Neural simulation adapt
    toks = re.findall(r"[A-Za-z]{3,}", goal)[:16]
    result.neural = {
        "learn": neural_simulation.experience(toks + (state.technology or [])),
        "activate": neural_simulation.activate(goal),
        "status": neural_simulation.status(),
    }

    result.perception = perception_bridge.status()
    result.meta = {
        "architecture": "OM_GENESIS_INTELLIGENCE_v1",
        "system_name": "OM (Operating Mind)",
        "hardware_enabled": bool(ctx.get("allow_hardware")) and not dry_run,
        "style": style,
        "assumption": state.clarification,
        "identity": identity_card(),
    }
    return result


def _compose_absolute_response(goal: str, state: Any, result: CycleResult) -> str:
    parts: list[str] = []
    if state.clarification:
        parts.append(f"*{state.clarification}*")

    from om_ai.understanding.query_kind import is_coding_task, is_definitional

    intent = getattr(state, "intent", "chat") or "chat"
    codingish = is_coding_task(goal) and not is_definitional(goal)

    coding_out = (result.agents or {}).get("coding_output") or ""
    user_face = (
        (result.cognition or {}).get("user_response")
        or (result.cognition or {}).get("answer")
        or ""
    )
    sol = (result.cognition or {}).get("solution") or ""
    grounded = (result.knowledge or {}).get("grounded_reply") or ""
    ksource = (result.knowledge or {}).get("source") or ""

    def _has_code(text: str) -> bool:
        return "```" in (text or "")

    if ksource == "fact_table" and grounded:
        parts.append(grounded.strip())
        return "\n\n".join(parts)

    if user_face.strip() and len(user_face.strip()) > 20:
        parts.append(user_face.strip())
        return "\n\n".join(parts)

    if codingish:
        if _has_code(coding_out):
            parts.append(coding_out.strip())
            return "\n\n".join(parts)
        if _has_code(sol):
            parts.append(sol.strip())
            return "\n\n".join(parts)

    if grounded and len(grounded) > 80 and (not codingish or _has_code(grounded)):
        parts.append(grounded.strip())
        return "\n\n".join(parts)

    if coding_out and len(coding_out) > 40 and _has_code(coding_out):
        parts.append(coding_out.strip())
        return "\n\n".join(parts)

    if sol and len(sol) > 80 and "Prefer smallest safe change" not in sol:
        from om_ai.core.response.response_formatter import looks_like_pipeline_dump

        if not looks_like_pipeline_dump(sol):
            parts.append(sol.strip())
            return "\n\n".join(parts)

    mem_bits = []
    for key in ("user", "project", "conversation"):
        for s in (result.memory or {}).get(key) or []:
            mem_bits.append(s)
            if len(mem_bits) >= 2:
                break
    if mem_bits:
        parts.append("\n".join(f"- {m[:180]}" for m in mem_bits))

    snippets = (result.knowledge or {}).get("snippets") or []
    if snippets and not codingish:
        parts.append("\n".join(f"- {s[:220]}" for s in snippets[:3]))

    if not parts:
        try:
            from om_ai.core.response.response_formatter import ResponseFormatter

            return ResponseFormatter().format_user_response({"question": goal})
        except Exception:
            return f"{goal[:200]}\n"

    return "\n\n".join(parts)
