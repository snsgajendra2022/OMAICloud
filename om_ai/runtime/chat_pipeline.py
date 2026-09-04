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
) -> dict[str, Any]:
    """Run the upgraded staged chat pipeline. Returns answer + stage meta."""
    q = (user_text or "").strip()
    stages: list[str] = []
    meta: dict[str, Any] = {"pipeline": "om-chat-pipeline-v2"}

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

    # ── 4. Action Layer (STEP 86) + Knowledge Brain (88) ─────────────
    stages.append("action")
    reasoning: dict[str, Any] = {}
    tool_text = ""
    draft = ""
    action_meta: dict[str, Any] = {}
    try:
        from om_ai.tools.intelligence import AutonomousActionLayer

        cap_id = str(intent.get("intent") or "chat")
        intent_to_cap = {
            "code_creation": "coding",
            "debugging": "coding",
            "creation": "coding",
            "explanation": "research",
            "research": "research",
            "question": "research",
            "planning": "planning",
            "comparison": "analysis",
            "calculation": "calculator",
            "date_request": "date",
            "prompt_generation": "prompt_generator",
            "recommendation": "recommendation",
            "conversation": "chat",
            "vision_analysis": "vision",
        }
        capability = {
            "capability": intent_to_cap.get(
                cap_id, "research" if cap_id != "chat" else "chat"
            )
        }
        tool_query = str(
            (lang_pack.get("meaning") or {}).get("retrieval_query")
            or (mk.get("meaning") or {}).get("retrieval_query")
            or q
        )
        # Keep original user text for tool decision (retrieval_query may drop math/date cues)
        action = AutonomousActionLayer(identity=actor or "default").run(
            q,
            context={
                "tenant_id": tenant_id,
                "project_root": ".",
                "actor": actor,
                "project_id": project_id,
                "original_query": q,
                "retrieval_query": tool_query,
            },
            intent=intent,
            capability=capability,
            understanding=understanding or {"action": "", "text": q},
        )
        tool_text = (action.response_context or "").strip()
        if not tool_text and action.execution:
            tool_text = str(action.execution.get("combined_text") or "").strip()
        action_meta = action.to_dict()
        meta["action"] = action_meta
        meta["tools"] = {
            "planned": action.tools_planned,
            "allowed": action.tools_allowed,
            "blocked": action.tools_blocked,
            "executed": (action.execution or {}).get("executed"),
            "ok": (action.execution or {}).get("ok"),
            "mode": action.mode,
        }
    except Exception as exc:
        logger.debug("action layer skipped: %s", exc)
        meta["action"] = {"error": str(exc)}
        meta["tools"] = {"error": str(exc)}
        # Legacy fallback
        try:
            from om_ai.core.intelligence.tool_planner import ToolPlanner, CAPABILITY_TOOLS
            from om_ai.tools.chat_runner import execute_planned_tools, format_tool_context

            capability = {"capability": "research"}
            tools_plan = ToolPlanner().plan(
                intent, capability, understanding or {"action": ""}, question=q
            )
            tool_out = execute_planned_tools(
                list(tools_plan.get("tools") or []),
                q,
                context={
                    "tenant_id": tenant_id,
                    "project_root": ".",
                    "actor": actor,
                    "project_id": project_id,
                },
            )
            tool_text = format_tool_context(tool_out) or str(
                tool_out.get("combined_text") or ""
            )
            meta["tools"] = {
                "planned": tools_plan.get("tools"),
                "executed": tool_out.get("executed"),
                "ok": tool_out.get("ok"),
            }
        except Exception as exc2:
            meta["tools"] = {"error": str(exc2)}

    # Knowledge brain enrichment (STEP 88) — skip for pure live/calc actions
    stages.append("knowledge_brain")
    skip_kb = str((action_meta or {}).get("mode") or "") in {"live", "action"} and set(
        (action_meta or {}).get("tools_allowed") or []
    ).issubset({"date", "calculator"})
    try:
        from om_ai.knowledge.brain import AdvancedKnowledgeBrain

        kb = AdvancedKnowledgeBrain()
        if skip_kb:
            meta["knowledge_brain"] = {"skipped": True, "reason": "calc_or_date"}
        else:
            kb_q = str(
                (lang_pack.get("meaning") or {}).get("retrieval_query") or q
            )
            kb_out = kb.retrieve(kb_q, k=5)
            kb_text = str(kb_out.get("text") or "").strip()
            if kb_text and kb_text not in (tool_text or ""):
                tool_text = (
                    f"{tool_text}\n\n## Knowledge Brain\n{kb_text}".strip()
                    if tool_text
                    else f"## Knowledge Brain\n{kb_text}"
                )
            try:
                from om_ai.understanding.query_kind import is_greeting

                if not is_greeting(q) and len(q) > 20:
                    kb.ingest(q, source="chat")
            except Exception:
                pass
            meta["knowledge_brain"] = {
                "ok": kb_out.get("ok"),
                "entities": kb_out.get("entities"),
                "verified": kb_out.get("verified"),
            }
    except Exception as exc:
        meta["knowledge_brain"] = {"error": str(exc)}

    if knowledge_text and knowledge_text not in (tool_text or "") and not skip_kb:
        tool_text = (
            f"{tool_text}\n\n## Cross-lingual knowledge\n{knowledge_text}".strip()
            if tool_text
            else f"## Cross-lingual knowledge\n{knowledge_text}"
        )

    if memory_ctx and not skip_kb:
        tool_text = (
            f"{tool_text}\n\n## Memory\n{memory_ctx}".strip()
            if tool_text
            else f"## Memory\n{memory_ctx}"
        )

    stages.append("reasoning")
    try:
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
        from om_ai.understanding.query_kind import is_greeting

        if not is_greeting(q):
            reason_q = str(
                (lang_pack.get("meaning") or {}).get("retrieval_query") or q
            )
            reasoning = run_reasoning_pipeline(reason_q, retrieve=True)
            draft = str(
                reasoning.get("solution")
                or reasoning.get("answer")
                or reasoning.get("user_response")
                or ""
            ).strip()
            md = str(reasoning.get("markdown") or "")
            if "```" in md and (not draft or "```" not in draft):
                draft = md
        meta["reasoning"] = {
            "has_solution": bool(draft),
            "score": reasoning.get("score"),
            "passed": reasoning.get("passed"),
        }
    except Exception as exc:
        logger.debug("reasoning engine skipped: %s", exc)
        meta["reasoning"] = {"error": str(exc)}

    if tool_text and (not draft or len(draft) < 60):
        draft = tool_text
    elif tool_text and draft and tool_text[:60] not in draft:
        prefer_tools = False
        try:
            from om_ai.runtime.chat_orchestrator import is_low_quality_reply

            prefer_tools = bool(is_low_quality_reply(draft))
        except Exception:
            prefer_tools = False
        if prefer_tools or intent.get("intent") in {
            "code_creation",
            "debugging",
            "research",
            "explanation",
            "date_request",
            "calculation",
        }:
            if prefer_tools or (action_meta.get("execution") or {}).get("ok"):
                draft = tool_text if prefer_tools else f"{draft}\n\n## Tool results\n{tool_text}"
            elif intent.get("intent") in {
                "code_creation",
                "debugging",
                "research",
                "explanation",
            }:
                draft = f"{draft}\n\n## Tool results\n{tool_text}"

    # ── 5. Model Generation ──────────────────────────────────────────
    stages.append("model")
    model_text = ""
    used_model = False
    need_model = not draft or len(draft) < 40
    try:
        from om_ai.understanding.query_kind import is_greeting

        if is_greeting(q):
            need_model = False
            if not draft:
                draft = "Hello — I’m OM. How can I help you?"
    except Exception:
        pass

    if need_model and native_ready and callable(native_chat):
        try:
            from om_ai.runtime.chat_orchestrator import build_chat_messages, is_low_quality_reply
            from om_ai.runtime.engine import usable_generation_text

            lang_instruction = str(lang_pack.get("instruction") or "").strip()
            sys_bits = ["You are OM AI."]
            if lang_instruction:
                sys_bits.append(lang_instruction)
            meaning = lang_pack.get("meaning") or {}
            if meaning.get("topic"):
                sys_bits.append(f"Topic: {meaning.get('topic')}.")
            if meaning.get("country"):
                sys_bits.append(f"Country/region: {meaning.get('country')}.")
            if intent.get("intent"):
                sys_bits.append(f"Intent: {intent.get('intent')}.")
            if memory_ctx:
                sys_bits.append("Relevant memory:\n" + memory_ctx[:800])
            if tool_text:
                sys_bits.append("Use tool results when relevant:\n" + tool_text[:1200])
            packed = build_chat_messages(
                messages or [{"role": "user", "content": q}],
                compact=True,
                extra_system="\n".join(sys_bits)[:1200],
            )
            gen_kwargs = dict(kwargs or {})
            raw = native_chat(packed, **gen_kwargs)
            model_text = (usable_generation_text(raw) or raw or "").strip()
            if model_text and not is_low_quality_reply(model_text):
                draft = model_text
                used_model = True
            meta["model"] = {"used": used_model, "len": len(model_text)}
        except Exception as exc:
            logger.debug("model generation skipped: %s", exc)
            meta["model"] = {"used": False, "error": str(exc)}
    else:
        meta["model"] = {
            "used": False,
            "reason": "draft_ready" if draft else "model_unavailable",
        }

    if not (draft or "").strip():
        stages.append("cognitive_fallback")
        try:
            from om_ai.core.intelligence import CognitiveIntelligence

            cog = CognitiveIntelligence().run(
                q,
                messages=messages,
                project=project_id,
            )
            draft = str(cog.get("answer") or "").strip()
            meta["cognitive"] = {
                "capability": (cog.get("capability") or {}).get("id"),
                "tools": (cog.get("plan") or {}).get("tools_executed"),
            }
        except Exception as exc:
            meta["cognitive"] = {"error": str(exc)}

    if not (draft or "").strip():
        try:
            from om_ai.agent.verifier import compose_fallback

            draft = compose_fallback(
                intent=str(intent.get("intent") or "chat"),
                user_text=q,
            )
        except Exception:
            draft = "Hello — I’m OM. How can I help you?"

    # Reject garbled/static drafts before language check + memory write
    try:
        from om_ai.runtime.chat_orchestrator import is_low_quality_reply

        bad = is_low_quality_reply(draft)
        if bad:
            meta["quality_reject"] = bad
            # Prefer real tool results over fallback chrome
            if tool_text and len(tool_text.strip()) >= 20:
                draft = tool_text.strip()
                meta["quality_recover"] = "tool_text"
            else:
                try:
                    from om_ai.agent.verifier import compose_fallback

                    draft = compose_fallback(
                        intent=str(intent.get("intent") or "chat"),
                        user_text=q,
                    )
                except Exception:
                    draft = (
                        "I understood your question — let me help with that. "
                        "Could you rephrase or add a bit more detail?"
                    )
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

    # ── 7. Final Answer polish ───────────────────────────────────────
    stages.append("final")
    try:
        from om_ai.response_engine import format_assistant_reply
        from om_ai.core.response.response_formatter import ensure_public_reply, response_mode

        intent_name = str(intent.get("intent") or "chat")
        polished = format_assistant_reply(draft, intent=intent_name, enhance=True)
        if response_mode() != "developer":
            polished = ensure_public_reply(
                q,
                polished,
                {"intent": intent, "understanding": understanding},
            )
        if polished and polished.strip():
            draft = polished.strip()
    except Exception as exc:
        logger.debug("final polish skipped: %s", exc)

    if not (draft or "").strip():
        draft = "Hello — I’m OM. How can I help you?"

    # ── 8. Memory write ──────────────────────────────────────────────
    stages.append("memory_write")
    if memory is not None:
        try:
            memory.remember_turn(q, draft)
            from om_ai.understanding.query_kind import is_greeting

            if not is_greeting(q) and len(draft) > 80:
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
