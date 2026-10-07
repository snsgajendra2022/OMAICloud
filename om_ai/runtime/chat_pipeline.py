"""
OM Chat Pipeline v2

User Message
  → Language Manager (+ multilingual meaning)
  → Advanced Memory recall
  → Intent Engine
  → Reasoning Engine (+ tools / knowledge)
  → Model Generation
  → Response Language Check
  → Final Answer
  → Memory write (turn + experience)
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable

logger = logging.getLogger(__name__)


def pipeline_enabled() -> bool:
    return os.environ.get("OM_CHAT_PIPELINE", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def run_chat_pipeline(
    user_text: str,
    *,
    messages: list[dict] | None = None,
    native_chat: Callable[..., str] | None = None,
    native_ready: bool = False,
    kwargs: dict[str, Any] | None = None,
    tenant_id: str = "default",
    actor: str = "",
    project_id: str | None = None,
    project_instructions: str = "",
    force_tools: list[str] | None = None,
    evolution_level: float | None = None,
    evolution_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the upgraded staged chat pipeline. Returns answer + stage meta."""
    q = (user_text or "").strip()
    stages: list[str] = []
    meta: dict[str, Any] = {"pipeline": "om-chat-pipeline-v2"}
    forced = [str(t).strip() for t in (force_tools or []) if str(t).strip()]
    meta["force_tools"] = forced
    profile = dict(evolution_profile or {})
    level = float(evolution_level if evolution_level is not None else profile.get("level") or 0) or None
    if level is not None:
        meta["evolution_level"] = level
        meta["evolution_model"] = profile.get("model_id")
        meta["evolution_style"] = profile.get("style")
    # Level knobs: Agent/Org lean on tools; Innovator/Org lean on live research; Reasoner on CoT.
    prefer_tools = bool(profile.get("prefer_tools"))
    prefer_research = bool(profile.get("prefer_research"))
    prefer_reasoning = bool(profile.get("prefer_reasoning"))
    prefer_planning = bool(profile.get("prefer_planning"))
    if prefer_tools and "web" not in forced:
        # Soft nudge — classifier still decides; UI can also force tools.
        meta["level_prefer_tools"] = True
    if prefer_research:
        meta["level_prefer_research"] = True
    if prefer_reasoning:
        meta["level_prefer_reasoning"] = True
    if prefer_planning:
        meta["level_prefer_planning"] = True

    # ── 0. STEP 26 OM Chat Intelligence Core (front door) ─────────────
    # User → Understand → Remember → Plan → Solve → Improve → Answer
    # Greetings / social never hit the small raw model.
    stages.append("step26_chat_intelligence")
    chat_intel: dict[str, Any] = {}
    try:
        from om_ai.core.chat_intelligence import run_chat_intelligence

        hist = []
        for m in messages or []:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").lower()
            content = str(m.get("content") or "").strip()
            if role in {"user", "assistant", "system"} and content:
                hist.append({"role": role, "content": content[:2000]})

        chat_intel = run_chat_intelligence(
            q,
            history=hist,
            tenant_id=tenant_id,
            actor=actor,
            model_generate=native_chat if native_ready else None,
            model_context="",
            extra={
                "project_id": project_id,
                "project_instructions": project_instructions,
            },
        ) or {}
        meta["chat_intelligence"] = {
            "intent": (chat_intel.get("intent") or {}),
            "strategy": (chat_intel.get("plan") or {}).get("strategy")
            or (chat_intel.get("meta") or {}).get("strategy"),
            "stages": list(chat_intel.get("stages") or []),
            "needs_model": bool(chat_intel.get("needs_model", True)),
            "social": bool((chat_intel.get("meta") or {}).get("social")),
            "quality": (chat_intel.get("meta") or {}).get("quality"),
            "confidence": (chat_intel.get("meta") or {}).get("confidence"),
        }
        ci_answer = str(chat_intel.get("answer") or "").strip()
        # Early return for greetings / identity / thanks — ChatGPT-like UX
        if ci_answer and not chat_intel.get("needs_model", True):
            stages.append("response")
            return {
                "answer": ci_answer if ci_answer.endswith("\n") else ci_answer + "\n",
                "stages": stages,
                "meta": meta,
                "language": {"language": "en", "response_language": "en"},
                "intent": chat_intel.get("intent") or {"intent": "conversation"},
                "chat_intelligence": chat_intel,
            }
        # Seed structured solution / plan into later stages
        ci_blob = str(chat_intel.get("context_blob") or "").strip()
        sol = chat_intel.get("solution") or {}
        if isinstance(sol, dict) and sol.get("answer"):
            meta["chat_intelligence_solution"] = str(sol.get("answer") or "")[:2000]
        if ci_blob:
            meta["chat_intelligence_context"] = ci_blob[:1200]
        if chat_intel.get("system_hint"):
            meta["chat_intelligence_hint"] = str(chat_intel.get("system_hint"))[:500]
    except Exception as exc:
        logger.debug("chat intelligence skipped: %s", exc)
        meta["chat_intelligence"] = {"error": str(exc)}

    # ── 0b. STEP 24 OM Brain Router ───────────────────────────────────
    # User → OM Brain → Fusion → Research → Knowledge → Agents → Response
    stages.append("step24_brain_router")
    step24: dict[str, Any] = {}
    try:
        from om_ai.core.brain_router import run_om_brain_router

        step24 = run_om_brain_router(
            q,
            context={
                "tenant_id": tenant_id,
                "actor": actor,
                "project_id": project_id,
                "project_instructions": project_instructions,
                "chat_intelligence": meta.get("chat_intelligence"),
            },
        ) or {}
        meta["step24"] = {
            "models": list(step24.get("models") or []),
            "knowledge_found": bool(step24.get("knowledge_found")),
            "research_used": bool(step24.get("research_used")),
            "agents": [
                (a.get("type") if isinstance(a, dict) else str(a))
                for a in (step24.get("agents") or [])
            ],
            "step26": (step24.get("meta") or {}).get("step26"),
        }
        blob = str(step24.get("context_blob") or "").strip()
        if blob:
            # Seed internal notes early; later stages append more.
            meta["step24_context"] = blob[:1200]
    except Exception as exc:
        logger.debug("step24 brain router skipped: %s", exc)
        meta["step24"] = {"error": str(exc)}

    # ── 0b. STEP 26 Autonomous Agent Runtime (reuse STEP 24 pack when present)
    stages.append("step26_agent_runtime")
    step26: dict[str, Any] = {}
    try:
        nested = (meta.get("step24") or {}).get("step26")
        if isinstance(nested, dict) and nested:
            step26 = {
                "goal": nested.get("goal"),
                "agents": list(nested.get("agents") or []),
                "meta": {"step": 26, "source": "step24"},
                "stages": ["agent_runtime", "from_step24"],
                "context_blob": "",
                "results": [],
            }
            meta["step26"] = {
                "agents": list(step26.get("agents") or []),
                "goal": step26.get("goal"),
                "source": "step24",
            }
        else:
            from om_ai.core.agent_runtime import run_agent_runtime

            step26 = run_agent_runtime(
                q,
                context={
                    "tenant_id": tenant_id,
                    "actor": actor,
                    "project_id": project_id,
                    "project_instructions": project_instructions,
                },
            ) or {}
            meta["step26"] = {
                "agents": list(step26.get("agents") or []),
                "goal": step26.get("goal"),
                "plan": step26.get("plan"),
                "result_count": len(step26.get("results") or []),
                "stages": list(step26.get("stages") or []),
                "source": "direct",
            }
            blob26 = str(step26.get("context_blob") or "").strip()
            if blob26:
                meta["step26_context"] = blob26[:1200]
    except Exception as exc:
        logger.debug("step26 agent runtime skipped: %s", exc)
        meta["step26"] = {"error": str(exc)}

    # ── 1. Language Manager (+ meaning) ───────────────────────────────
    stages.append("language")
    lang_pack: dict[str, Any] = {
        "language": "en",
        "response_language": "en",
        "instruction": "Reply in English.",
        "analysis": {},
        "meaning": {},
    }
    try:
        from om_ai.language import LanguageManager

        lang_pack = LanguageManager().process(q)
    except Exception as exc:
        logger.debug("language manager skipped: %s", exc)
    meta["language"] = lang_pack

    # ── 1b. Multilingual knowledge (Language → Meaning → Retrieval) ──
    stages.append("multilingual_knowledge")
    mk: dict[str, Any] = {}
    knowledge_text = ""
    try:
        from om_ai.language.meaning import MultilingualKnowledge

        mk = MultilingualKnowledge().understand(
            q,
            language=str(lang_pack.get("language") or "en"),
        )
        knowledge_text = str(mk.get("knowledge_text") or "").strip()
        if not lang_pack.get("meaning"):
            lang_pack["meaning"] = mk.get("meaning") or {}
    except Exception as exc:
        logger.debug("multilingual knowledge skipped: %s", exc)
        mk = {"error": str(exc)}
    meta["multilingual_knowledge"] = {
        "meaning": (mk.get("meaning") if isinstance(mk, dict) else None),
        "hits": len((mk.get("knowledge") or []) if isinstance(mk, dict) else []),
    }

    # ── 2. Advanced Memory recall ────────────────────────────────────
    stages.append("memory")
    memory_ctx = ""
    memory = None
    try:
        from om_ai.memory.memory_manager import AdvancedMemorySystem, advanced_memory_enabled

        if advanced_memory_enabled():
            memory = AdvancedMemorySystem(
                tenant_id=tenant_id or "default",
                user_id=actor or "default",
                project_id=project_id,
            )
            retrieval_q = str(
                (lang_pack.get("meaning") or {}).get("retrieval_query")
                or (mk.get("meaning") or {}).get("retrieval_query")
                or q
            )
            memory_ctx = memory.context_for_prompt(retrieval_q, limit=6)
            meta["memory"] = {
                "enabled": True,
                "snippet_chars": len(memory_ctx),
            }
        else:
            meta["memory"] = {"enabled": False}
    except Exception as exc:
        logger.debug("advanced memory skipped: %s", exc)
        meta["memory"] = {"error": str(exc)}

    # ── 3. Intent Engine ─────────────────────────────────────────────
    stages.append("intent")
    intent: dict[str, Any] = {"intent": "chat", "domain": "general", "confidence": 0.5}
    understanding: dict[str, Any] = {}
    try:
        from om_ai.core.intelligence.understanding_engine import UnderstandingEngine
        from om_ai.core.intelligence.intent_engine import IntentEngine

        meaning = lang_pack.get("meaning") or {}
        understanding = UnderstandingEngine().understand(
            q,
            context={
                "project_hint": project_instructions or "",
                "topic": meaning.get("topic"),
                "country": meaning.get("country"),
                "cross_lingual_intent": meaning.get("intent"),
            },
        )
        intent = IntentEngine().resolve(understanding)
        if meaning.get("intent") and meaning["intent"] != "general":
            if str(intent.get("intent") or "") in {"chat", "conversation", "question"}:
                intent = {
                    **intent,
                    "intent": {
                        "future_analysis": "research",
                        "explanation": "explanation",
                        "how_to": "planning",
                        "comparison": "comparison",
                        "recommendation": "recommendation",
                    }.get(str(meaning["intent"]), intent.get("intent")),
                    "domain": meaning.get("topic") or intent.get("domain"),
                }
    except Exception as exc:
        logger.debug("intent engine skipped: %s", exc)
        try:
            from om_ai.understanding.query_kind import query_kind

            intent = {"intent": query_kind(q), "domain": "general", "confidence": 0.6}
        except Exception:
            pass
    meta["intent"] = intent
    meta["understanding"] = understanding

    # ── 3a. Tool Decision Layer (ContextIntentClassifier) ────────────
    stages.append("tool_decision")
    ctx_intent: dict[str, Any] = {"intent": "general", "use_tools": False, "tools": []}
    try:
        from om_ai.core.understanding.context_intent import classify_context_intent

        ctx_intent = classify_context_intent(q)
        if forced:
            ctx_intent["use_tools"] = True
            ctx_intent["tools"] = list(
                dict.fromkeys(list(ctx_intent.get("tools") or []) + forced)
            )
            ctx_intent["reason"] = str(ctx_intent.get("reason") or "") + "+ui_tools"
        # OM-L3 / OM-L5: lean toward tools for actionable asks (not pure greetings).
        if prefer_tools and not ctx_intent.get("use_tools"):
            qlow = q.lower()
            actionable = any(
                w in qlow
                for w in (
                    "calculate",
                    "compute",
                    "run",
                    "code",
                    "script",
                    "search",
                    "find",
                    "build",
                    "create",
                    "fix",
                    "debug",
                    "plan",
                    "budget",
                    "%",
                    "+",
                    "*",
                )
            ) or bool(re.search(r"\d+\s*[\+\-\*/]\s*\d+", q))
            if actionable:
                ctx_intent["use_tools"] = True
                tools = list(ctx_intent.get("tools") or [])
                if "code" not in tools:
                    tools.append("code")
                ctx_intent["tools"] = tools
                ctx_intent["reason"] = str(ctx_intent.get("reason") or "") + "+level_agent"
        if ctx_intent.get("intent") == "conversation":
            intent = {
                **intent,
                "intent": "conversation",
                "canonical": "conversation",
                "domain": "social",
                "confidence": 0.95,
            }
            meta["intent"] = intent
        elif ctx_intent.get("intent") == "date_query":
            intent = {
                **intent,
                "intent": "date_request",
                "canonical": "date_request",
                "domain": "time",
                "confidence": 0.95,
            }
            meta["intent"] = intent
        meta["tool_decision"] = ctx_intent
    except Exception as exc:
        meta["tool_decision"] = {"error": str(exc)}

    # ── 3a2. Live web/Wikipedia + helpful defaults (beat stale Genesis) ─
    stages.append("live_knowledge")
    preferred_draft = ""
    live_pack: dict[str, Any] = {}
    try:
        from om_ai.runtime.live_answer import (
            fetch_live_pack,
            needs_live_knowledge,
            live_enabled,
            network_enabled,
        )
        from om_ai.core.intelligence.real_answer import from_helpful_defaults, from_facts
        from om_ai.runtime.public_reply import looks_like_genesis_template

        preferred = ""
        # L4/L5 prefer live research more often; L1 stays conservative.
        want_live = needs_live_knowledge(q)
        if prefer_research and not want_live:
            qlow = q.lower()
            want_live = any(
                w in qlow
                for w in (
                    "what is",
                    "who is",
                    "latest",
                    "current",
                    "research",
                    "invent",
                    "novel",
                    "compare",
                    "versus",
                    "vs ",
                )
            )
        if level is not None and abs(float(level) - 1.0) < 0.01:
            # Chatbot: only live when clearly freshness-sensitive.
            want_live = want_live and any(
                w in q.lower()
                for w in ("latest", "current", "today", "news", "version", "release")
            )
        if live_enabled() and network_enabled() and want_live:
            live_pack = fetch_live_pack(q, limit=5)
            if live_pack.get("ok") and live_pack.get("answer"):
                preferred = str(live_pack["answer"]).strip()
                internal_live = str(live_pack.get("context") or "")[:1200]
                if internal_live:
                    meta["live_context_stash"] = internal_live
            meta["live_knowledge"] = {
                "used": bool(preferred),
                "sources": len(live_pack.get("sources") or []),
                "wikipedia": bool(live_pack.get("wikipedia")),
            }
        else:
            meta["live_knowledge"] = {
                "used": False,
                "enabled": live_enabled(),
                "network": network_enabled(),
            }

        # Merge live + local: prefer live for definitions/versions when strong
        local = from_helpful_defaults(q) or from_facts(q) or ""
        if preferred and local:
            qlow = q.lower()
            wants_fresh = any(
                w in qlow
                for w in (
                    "latest",
                    "current",
                    "version",
                    "verion",
                    "lestest",
                    "news",
                    "today",
                    "release",
                )
            )
            live_strong = bool(live_pack.get("wikipedia")) or "Sources:" in preferred
            if wants_fresh or live_strong:
                # keep live preferred
                pass
            elif len(local) > len(preferred) + 80:
                preferred = local
        if not preferred:
            preferred = local

        if preferred and not looks_like_genesis_template(preferred):
            preferred_draft = preferred.strip()
            meta["helpful_defaults"] = {
                "used": True,
                "chars": len(preferred_draft),
                "source": "live" if live_pack.get("ok") else "local",
            }
        else:
            meta["helpful_defaults"] = {"used": False}

        # Prefer Chat Intelligence solution for debugging / structured asks
        ci_sol = str(meta.get("chat_intelligence_solution") or "").strip()
        ci_intent = str(((meta.get("chat_intelligence") or {}).get("intent") or {}).get("intent") or "")
        if ci_sol and (
            ci_intent in {"debugging", "coding", "howto", "comparison", "explain"}
            or len(ci_sol) > len(preferred_draft or "")
        ):
            if not preferred_draft or ci_intent == "debugging" or len(ci_sol) >= 80:
                preferred_draft = ci_sol
                meta["helpful_defaults"] = {
                    "used": True,
                    "chars": len(preferred_draft),
                    "source": "chat_intelligence",
                }
    except Exception as exc:
        meta["live_knowledge"] = {"error": str(exc)}
        meta["helpful_defaults"] = {"error": str(exc)}

    # ── 3b. Connectivity INTERNAL ONLY (never shown to user) ─────────
    stages.append("system_connectivity")
    internal_context = ""
    try:
        if forced or ctx_intent.get("intent") not in {"conversation", "date_query", "calculation"}:
            from om_ai.runtime.connectivity_bridge import enrich_chat_turn

            connectivity = enrich_chat_turn(
                q,
                context={
                    "tenant_id": tenant_id,
                    "actor": actor,
                    "project_id": project_id,
                    "project_root": ".",
                },
                intent=intent,
            )
            block = str(connectivity.get("context_block") or "").strip()
            if block:
                internal_context = block[:1200]
            meta["connectivity"] = {
                "enabled": connectivity.get("enabled"),
                "connected_count": connectivity.get("connected_count"),
                "internal_only": True,
            }
        else:
            meta["connectivity"] = {"skipped": True, "reason": ctx_intent.get("intent")}
    except Exception as exc:
        meta["connectivity"] = {"error": str(exc)}

    # ── 4. Action / tools (public clean answers only) ────────────────
    stages.append("action")
    reasoning: dict[str, Any] = {}
    public_tool = ""
    draft = preferred_draft or ""
    action_meta: dict[str, Any] = {}
    try:
        from om_ai.tools.intelligence import AutonomousActionLayer
        from om_ai.runtime.public_reply import extract_clean_tool_answer

        cap_from_ctx = {
            "date_query": "date",
            "conversation": "chat",
            "calculation": "calculator",
            "coding": "coding",
            "research": "chat",
            "general": "chat",
        }
        capability = {"capability": cap_from_ctx.get(str(ctx_intent.get("intent") or "general"), "chat")}

        # Skip tools only for pure chat when the user did not enable Web/Code.
        skip_tools = (not forced) and (
            ctx_intent.get("intent") == "conversation"
            or (
                not ctx_intent.get("use_tools")
                and ctx_intent.get("intent") in {"general", "research"}
            )
        )
        if skip_tools:
            meta["tools"] = {
                "planned": [],
                "allowed": [],
                "executed": [],
                "ok": False,
                "mode": "answer",
                "reason": ctx_intent.get("reason"),
            }
            action_meta = {"mode": "answer", "needs_tools": False, "tools_allowed": []}
            meta["action"] = action_meta
        else:
            action = AutonomousActionLayer(identity=actor or "default").run(
                q,
                context={
                    "tenant_id": tenant_id,
                    "project_root": ".",
                    "actor": actor,
                    "project_id": project_id,
                    "original_query": q,
                    "force_tools": forced or list(ctx_intent.get("tools") or []),
                },
                intent=intent,
                capability=capability,
                understanding=understanding or {"action": "", "text": q},
            )
            raw_tool = (action.response_context or "").strip()
            if not raw_tool and action.execution:
                raw_tool = str(action.execution.get("combined_text") or "").strip()
            public_tool = extract_clean_tool_answer(raw_tool)
            if forced and not public_tool and not (action.execution or {}).get("executed"):
                from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context

                direct = execute_planned_tools(
                    forced,
                    q,
                    context={
                        "tenant_id": tenant_id,
                        "project_root": ".",
                        "actor": actor,
                        "project_id": project_id,
                    },
                )
                public_tool = extract_clean_tool_answer(
                    format_tool_context(direct) or str(direct.get("combined_text") or "")
                )
                meta["tools_direct"] = {
                    "executed": direct.get("executed"),
                    "ok": direct.get("ok"),
                    "skipped": direct.get("skipped"),
                }
            action_meta = action.to_dict()
            meta["action"] = action_meta
            meta["tools"] = {
                "planned": action.tools_planned,
                "allowed": action.tools_allowed,
                "blocked": action.tools_blocked,
                "executed": (action.execution or {}).get("executed"),
                "ok": (action.execution or {}).get("ok") or bool(public_tool),
                "mode": action.mode,
                "forced": forced,
            }
    except Exception as exc:
        logger.debug("action layer skipped: %s", exc)
        meta["action"] = {"error": str(exc)}
        meta["tools"] = {"error": str(exc)}
        if forced:
            try:
                from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context
                from om_ai.runtime.public_reply import extract_clean_tool_answer as _clean

                direct = execute_planned_tools(
                    forced,
                    q,
                    context={"tenant_id": tenant_id, "project_root": ".", "actor": actor},
                )
                public_tool = _clean(
                    format_tool_context(direct) or str(direct.get("combined_text") or "")
                )
                meta["tools_direct"] = {
                    "executed": direct.get("executed"),
                    "ok": direct.get("ok"),
                }
            except Exception as exc2:
                meta["tools_direct"] = {"error": str(exc2)}

    # Knowledge / memory → internal only
    stages.append("knowledge_brain")
    skip_kb = ctx_intent.get("intent") in {"conversation", "date_query", "calculation"}
    try:
        from om_ai.knowledge.brain import AdvancedKnowledgeBrain

        kb = AdvancedKnowledgeBrain()
        if skip_kb:
            meta["knowledge_brain"] = {"skipped": True, "reason": ctx_intent.get("intent")}
        else:
            kb_out = kb.retrieve(str((lang_pack.get("meaning") or {}).get("retrieval_query") or q), k=5)
            kb_text = str(kb_out.get("text") or "").strip()
            if kb_text:
                internal_context = (internal_context + "\n" + kb_text[:1000]).strip()
            meta["knowledge_brain"] = {"ok": kb_out.get("ok"), "internal_only": True}
            if len(q) > 20:
                try:
                    kb.ingest(q, source="chat")
                except Exception:
                    pass
    except Exception as exc:
        meta["knowledge_brain"] = {"error": str(exc)}

    if knowledge_text and not skip_kb:
        internal_context = (internal_context + "\n" + knowledge_text[:600]).strip()
    if memory_ctx and not skip_kb:
        internal_context = (internal_context + "\n" + memory_ctx[:600]).strip()
    stash = str(meta.get("live_context_stash") or "").strip()
    if stash and not skip_kb:
        internal_context = (internal_context + "\n" + stash).strip()
    step24_ctx = str(meta.get("step24_context") or "").strip()
    if step24_ctx and not skip_kb:
        internal_context = (internal_context + "\n" + step24_ctx).strip()
    step26_ctx = str(meta.get("step26_context") or "").strip()
    if step26_ctx and not skip_kb:
        internal_context = (internal_context + "\n" + step26_ctx).strip()
    ci_sol = str(meta.get("chat_intelligence_solution") or "").strip()
    if ci_sol and not skip_kb:
        internal_context = (internal_context + "\n" + ci_sol).strip()
    ci_ctx = str(meta.get("chat_intelligence_context") or "").strip()
    if ci_ctx and not skip_kb:
        internal_context = (internal_context + "\n" + ci_ctx).strip()
    ci_hint = str(meta.get("chat_intelligence_hint") or "").strip()
    if ci_hint and not skip_kb:
        internal_context = (internal_context + "\n" + ci_hint).strip()
    if prefer_planning and not skip_kb and len(q) > 40:
        internal_context = (
            internal_context
            + "\nOrganization mode: structure complex work as goal → owners → ordered steps → risks."
        ).strip()
        meta["planning_hint"] = True

    stages.append("reasoning")
    try:
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
        from om_ai.understanding.query_kind import is_greeting

        run_reason = (
            not is_greeting(q)
            and ctx_intent.get("intent") not in {"conversation", "date_query", "calculation"}
        )
        # L1 skips deep reasoning for short chatty asks; L2+ lean into it.
        if level is not None and abs(float(level) - 1.0) < 0.01 and len(q) < 80:
            run_reason = False
            meta["reasoning_skip"] = "level1_chatbot"
        elif prefer_reasoning and not is_greeting(q):
            run_reason = True
        if run_reason:
            reasoning = run_reasoning_pipeline(
                str((lang_pack.get("meaning") or {}).get("retrieval_query") or q),
                retrieve=True,
            )
            reasoned = str(
                reasoning.get("solution")
                or reasoning.get("answer")
                or reasoning.get("user_response")
                or ""
            ).strip()
            md = str(reasoning.get("markdown") or "")
            if "```" in md and (not reasoned or "```" not in reasoned):
                reasoned = md
            # Keep curated fact/default answers; don't let weak reasoning replace them
            if preferred_draft and len(preferred_draft) >= 40:
                if "```" in reasoned and "```" not in preferred_draft:
                    draft = reasoned
                else:
                    draft = preferred_draft
            elif reasoned:
                draft = reasoned
        meta["reasoning"] = {
            "has_solution": bool(draft),
            "kept_preferred": bool(preferred_draft and draft == preferred_draft),
        }
    except Exception as exc:
        meta["reasoning"] = {"error": str(exc)}

    if public_tool:
        try:
            from om_ai.runtime.public_reply import looks_like_genesis_template, is_safe_public_answer

            if looks_like_genesis_template(public_tool) or not is_safe_public_answer(public_tool):
                public_tool = ""
                meta["public_tool_rejected"] = "unsafe_or_genesis"
            elif not (draft or "").strip():
                draft = public_tool
            elif len(public_tool) > len(draft) + 40 and "react" in public_tool.lower():
                # Prefer curated fact/tool answer over weak draft
                draft = public_tool
        except Exception:
            if not (draft or "").strip():
                draft = public_tool

    # ── 5. Model Generation (uses internal_context privately) ────────
    stages.append("model")
    model_text = ""
    used_model = False
    need_model = not draft or len(draft) < 40
    if preferred_draft and len(preferred_draft) >= 40 and draft == preferred_draft:
        need_model = False
        meta["model_skip"] = "preferred_draft"

    if ctx_intent.get("intent") == "conversation":
        need_model = False
        low = q.lower()
        if "morning" in low or "moring" in low:
            draft = "Good morning! I’m doing well — thanks for asking. How can I help you today?"
        elif "evening" in low:
            draft = "Good evening! Hope your day’s been good. What would you like to work on?"
        elif re.search(r"\bhow\s+(was|is|are)\b", low):
            draft = "I’m doing well — thanks for asking! How can I help you today?"
        else:
            draft = "Hello — I’m OM. How can I help you?"

    if need_model and native_ready and callable(native_chat):
        try:
            from om_ai.runtime.chat_orchestrator import build_chat_messages, is_low_quality_reply
            from om_ai.runtime.engine import usable_generation_text
            from om_ai.runtime.public_reply import sanitize_public_reply, is_safe_public_answer

            sys_bits = ["You are OM AI. Reply helpfully in plain language."]
            lang_instruction = str(lang_pack.get("instruction") or "").strip()
            if lang_instruction:
                sys_bits.append(lang_instruction)
            if intent.get("intent"):
                sys_bits.append(f"Intent: {intent.get('intent')}.")
            if public_tool:
                sys_bits.append("Verified tool result:\n" + public_tool[:400])
            if internal_context:
                sys_bits.append(
                    "Internal notes (do not repeat headers, paths, or dumps; paraphrase only):\n"
                    + internal_context[:800]
                )
            packed = build_chat_messages(
                messages or [{"role": "user", "content": q}],
                compact=True,
                extra_system="\n".join(sys_bits)[:1400],
            )
            raw = native_chat(packed, **dict(kwargs or {}))
            model_text = (usable_generation_text(raw) or raw or "").strip()
            model_text = sanitize_public_reply(model_text)
            if model_text and is_safe_public_answer(model_text) and not is_low_quality_reply(model_text):
                draft = model_text
                used_model = True
            meta["model"] = {"used": used_model, "len": len(model_text or "")}
        except Exception as exc:
            meta["model"] = {"used": False, "error": str(exc)}
    else:
        meta["model"] = {"used": False, "reason": "draft_ready" if draft else "model_unavailable"}

    if not (draft or "").strip() and public_tool:
        draft = public_tool

    if not (draft or "").strip():
        try:
            from om_ai.agent.verifier import compose_fallback

            draft = compose_fallback(
                intent=str(intent.get("intent") or "chat"),
                user_text=q,
            )
        except Exception:
            draft = "Hello — I’m OM. How can I help you?"

    # Never echo gibberish / user text back as the answer
    if (draft or "").strip().lower() == q.lower() or (
        len(q.split()) <= 2 and (draft or "").strip().lower() == q.lower()
    ):
        draft = "How can I help you today?"

    # Quality + public sanitize (never leak internals)
    try:
        from om_ai.runtime.public_reply import sanitize_public_reply, is_safe_public_answer, extract_clean_tool_answer
        from om_ai.runtime.chat_orchestrator import is_low_quality_reply

        draft = sanitize_public_reply(draft) or draft
        if public_tool and (not is_safe_public_answer(draft) or is_low_quality_reply(draft)):
            draft = public_tool
            meta["quality_recover"] = "public_tool"
        elif not is_safe_public_answer(draft) or is_low_quality_reply(draft or ""):
            recovered = ""
            try:
                from om_ai.core.intelligence.real_answer import build_real_answer
                from om_ai.runtime.public_reply import looks_like_genesis_template

                recovered = (build_real_answer(q, prefer_coding=("react" in q.lower() or "dashboard" in q.lower() or "create" in q.lower())) or "").strip()
                if looks_like_genesis_template(recovered):
                    recovered = ""
            except Exception:
                recovered = ""
            if recovered:
                draft = recovered
                meta["quality_recover"] = "real_answer"
            elif ctx_intent.get("intent") == "conversation":
                draft = "Hello — I’m OM. How can I help you?"
                meta["quality_reject"] = "unsafe_or_garble"
            else:
                draft = (
                    "I'm with you — that last draft wasn't solid. "
                    "Tell me what you need in your own words and I'll take it from there."
                )
                meta["quality_reject"] = "unsafe_or_garble"
    except Exception:
        pass

    # ── 6. Response Language Check ───────────────────────────────────
    stages.append("response_language_check")
    try:
        from om_ai.language import LanguageManager

        checked = LanguageManager().ensure_response_language(
            draft,
            target_language=str(lang_pack.get("response_language") or "en"),
            user_text=q,
        )
        draft = str(checked.get("answer") or draft)
        meta["response_language_check"] = {
            "ok": checked.get("ok"),
            "status": checked.get("status"),
            "target": checked.get("target_language"),
        }
    except Exception as exc:
        meta["response_language_check"] = {"error": str(exc)}

    # ── 7. Final polish + hard public sanitize ───────────────────────
    stages.append("final")
    try:
        from om_ai.response_engine import format_assistant_reply
        from om_ai.core.response.response_formatter import ensure_public_reply, response_mode
        from om_ai.runtime.public_reply import sanitize_public_reply, is_safe_public_answer

        intent_name = str(intent.get("intent") or "chat")
        polished = format_assistant_reply(draft, intent=intent_name, enhance=True)
        if response_mode() != "developer":
            polished = ensure_public_reply(
                q,
                polished,
                {"intent": intent, "understanding": understanding},
            )
        polished = sanitize_public_reply(polished or "") or polished
        if polished and is_safe_public_answer(polished):
            draft = polished.strip()
        elif public_tool:
            draft = public_tool
        elif ctx_intent.get("intent") == "conversation":
            draft = "Hello — I’m OM. How can I help you?"
    except Exception as exc:
        logger.debug("final polish skipped: %s", exc)

    # Absolute last gate — never show internals
    try:
        from om_ai.runtime.public_reply import sanitize_public_reply, is_safe_public_answer

        draft = sanitize_public_reply(draft) or draft
        if not is_safe_public_answer(draft):
            try:
                from om_ai.core.intelligence.real_answer import build_real_answer
                recovered = (build_real_answer(q) or "").strip()
                if recovered and is_safe_public_answer(recovered):
                    draft = recovered
                elif public_tool and is_safe_public_answer(public_tool):
                    draft = public_tool
                elif ctx_intent.get("intent") == "conversation":
                    draft = "Hello — I’m OM. How can I help you?"
                else:
                    draft = "How can I help you today?"
            except Exception:
                if public_tool:
                    draft = public_tool
                elif ctx_intent.get("intent") == "conversation":
                    draft = "Hello — I’m OM. How can I help you?"
                else:
                    draft = "How can I help you today?"
    except Exception:
        pass

    if not (draft or "").strip():
        draft = "Hello — I’m OM. How can I help you?"

    # Final understandability gate — never ship model gibberish
    try:
        from om_ai.runtime.chat_orchestrator import is_low_quality_reply, is_garbled_generation
        from om_ai.runtime.public_reply import looks_like_genesis_template, is_safe_public_answer
        from om_ai.core.intelligence.real_answer import build_real_answer

        bad = (
            not is_safe_public_answer(draft)
            or looks_like_genesis_template(draft)
            or bool(is_low_quality_reply(draft))
            or is_garbled_generation(draft)
            or (draft or "").strip().lower() == q.lower()
        )
        if bad:
            recovered = (
                str(meta.get("chat_intelligence_solution") or "").strip()
                or preferred_draft
                or (build_real_answer(q, prefer_coding=True) or "")
            )
            recovered = (recovered or "").strip()
            if recovered and is_safe_public_answer(recovered) and not looks_like_genesis_template(recovered) and not is_garbled_generation(recovered):
                draft = recovered
                meta["final_recover"] = "chat_intelligence_or_preferred"
            else:
                try:
                    from om_ai.core.chat_intelligence import CorrectionEngine

                    fixed = CorrectionEngine().correct(
                        q,
                        draft,
                        solution={"answer": str(meta.get("chat_intelligence_solution") or "")},
                        intent=str(((meta.get("chat_intelligence") or {}).get("intent") or {}).get("intent") or ""),
                    )
                    draft = str(fixed.get("answer") or draft)
                    meta["final_recover"] = fixed.get("reason") or "correction_engine"
                except Exception:
                    meta["final_recover"] = "clarify"
    except Exception as exc:
        meta["final_recover"] = {"error": str(exc)}

    # Chat Intelligence post-pass: optimize + safety on final draft
    try:
        from om_ai.core.chat_intelligence import ResponseOptimizer, SafetyFilter

        intent_name = str(
            ((meta.get("chat_intelligence") or {}).get("intent") or {}).get("intent")
            or ((meta.get("intent") or {}).get("intent") if isinstance(meta.get("intent"), dict) else "")
            or "chat"
        )
        opt = ResponseOptimizer().optimize(
            draft,
            message=q,
            intent=intent_name,
            fallback=str(meta.get("chat_intelligence_solution") or preferred_draft or ""),
        )
        draft = str(opt.get("answer") or draft)
        draft = SafetyFilter().filter(draft).get("answer") or draft
        meta["chat_intelligence_final"] = {
            "optimized": bool(opt.get("changed")),
            "report": opt.get("report"),
        }
    except Exception as exc:
        meta["chat_intelligence_final"] = {"error": str(exc)}

    # STEP 27 — Response Intelligence Upgrade
    try:
        from om_ai.core.response.response_intelligence import run_response_intelligence

        intent_name = str(
            ((meta.get("chat_intelligence") or {}).get("intent") or {}).get("intent")
            or "chat"
        )
        strategy = str(
            ((meta.get("chat_intelligence") or {}).get("strategy") or "")
        )
        ri = run_response_intelligence(q, draft, intent=intent_name, strategy=strategy)
        if ri.get("answer"):
            draft = str(ri["answer"])
        meta["response_intelligence"] = {
            "kind": ri.get("kind"),
            "strategy": ri.get("strategy"),
            "improved": ri.get("improved"),
        }
    except Exception as exc:
        meta["response_intelligence"] = {"error": str(exc)}

    # STEP 29 — Continuous learning observe (non-blocking)
    try:
        from om_ai.core.continuous_learning import run_continuous_learning

        learn = run_continuous_learning(
            q,
            draft,
            quality=(meta.get("response_intelligence") or {}).get("fact_check")
            if isinstance((meta.get("response_intelligence") or {}).get("fact_check"), dict)
            else meta.get("chat_intelligence_final", {}).get("report"),
        )
        meta["continuous_learning"] = {
            "observed": bool(learn.get("observed")),
            "failed": bool(((learn.get("observed") or {}).get("analysis") or {}).get("failed")),
        }
    except Exception as exc:
        meta["continuous_learning"] = {"error": str(exc)}

    # STEP 31 — Tool intelligence hint (metadata only unless tools forced)
    try:
        from om_ai.core.tool_intelligence import run_tool_intelligence

        tools = run_tool_intelligence(q)
        meta["tool_intelligence"] = {
            "needs_tools": tools.get("needs_tools"),
            "tools": tools.get("tools"),
        }
    except Exception as exc:
        meta["tool_intelligence"] = {"error": str(exc)}

    # ── 8. Memory write (store clean reply only) ─────────────────────
    stages.append("memory_write")
    if memory is not None:
        try:
            memory.remember_turn(q, draft)
            from om_ai.understanding.query_kind import is_greeting

            if not is_greeting(q) and len(draft) > 80 and ctx_intent.get("intent") != "conversation":
                memory.remember_experience(q, draft, score=0.7)
            meta["memory_write"] = {"ok": True}
        except Exception as exc:
            meta["memory_write"] = {"error": str(exc)}

    meta["stages"] = stages
    return {
        "answer": draft.strip() + "\n",
        "intent": intent,
        "language": lang_pack,
        "meta": meta,
        "stages": stages,
    }
