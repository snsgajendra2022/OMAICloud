"""OM Chat Intelligence Orchestrator — STEP 26 conversation brain."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable

from .answer_planner import AnswerPlanner
from .chat_quality_engine import ChatQualityEngine
from .confidence_engine import ConfidenceEngine
from .context_manager import ContextManager
from .conversation_engine import ConversationEngine
from .conversation_memory import ConversationMemory
from .correction_engine import CorrectionEngine
from .intent_understanding import IntentUnderstanding
from .personality_engine import PersonalityEngine
from .response_optimizer import ResponseOptimizer
from .safety_filter import SafetyFilter
from .solution_engine import SolutionEngine
from .user_preference import UserPreference

logger = logging.getLogger(__name__)


def _env_on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _supports_kw(fn: Callable[..., Any], name: str) -> bool:
    try:
        import inspect

        sig = inspect.signature(fn)
        if name in sig.parameters:
            return True
        return any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
    except Exception:
        return False


class ChatOrchestrator:
    """
    ChatGPT-style conversation brain:

      User message
        → Understand intention
        → Remember conversation
        → Decide answer strategy
        → Find solution
        → Generate answer (model optional)
        → Check quality
        → Improve / correct
        → Final response
    """

    def __init__(self) -> None:
        self.intent = IntentUnderstanding()
        self.conversation = ConversationEngine()
        self.memory = ConversationMemory()
        self.context = ContextManager()
        self.personality = PersonalityEngine()
        self.preferences = UserPreference()
        self.planner = AnswerPlanner()
        self.solutions = SolutionEngine()
        self.optimizer = ResponseOptimizer()
        self.correction = CorrectionEngine()
        self.confidence = ConfidenceEngine()
        self.quality = ChatQualityEngine()
        self.safety = SafetyFilter()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "step": 26,
            "name": "OM Chat Intelligence Core",
            "components": {
                "conversation_engine": True,
                "intent_understanding": True,
                "context_manager": True,
                "personality_engine": True,
                "answer_planner": True,
                "solution_engine": True,
                "problem_analyzer": True,
                "hypothesis_engine": True,
                "solution_planner": True,
                "reasoning_engine": True,
                "explanation_engine": True,
                "verification_engine": True,
                "confidence_engine": True,
                "correction_engine": True,
                "solution_memory": True,
                "response_optimizer": True,
                "conversation_memory": True,
                "user_preference": True,
                "chat_quality_engine": True,
                "safety_filter": True,
            },
        }

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        tenant_id: str = "default",
        actor: str = "",
        model_generate: Callable[..., str] | None = None,
        model_context: str = "",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q = (message or "").strip()
        stages: list[str] = ["chat_intelligence"]
        meta: dict[str, Any] = {
            "step": 26,
            "flow": "understand→remember→plan→solve→generate→quality→improve→answer",
        }
        session = self.memory.session_id(tenant_id, actor)
        user_key = session

        if not q:
            return {
                "answer": "",
                "handled": False,
                "stages": stages + ["empty"],
                "meta": {**meta, "empty": True},
                "intent": {"intent": "empty"},
            }

        # 0) STEP 71 — Human Presence (why before what)
        stages.append("human_presence")
        presence: dict[str, Any] = {}
        try:
            from om_ai.core.human_presence import run_human_presence

            locale = "hi" if any(
                w in q.lower() for w in ("hai", "kya", "tum", "nahi", "thak", "bhai")
            ) else "en"
            presence = run_human_presence(q, history=history, locale=locale) or {}
            meta["human_presence"] = {
                "route": (presence.get("route") or {}).get("mode"),
                "listen_first": presence.get("listen_first"),
                "emotion": (presence.get("emotion") or {}).get("emotion"),
                "intent": (presence.get("intent") or {}).get("intent"),
            }
            # Sharing / listen-first → natural reply; skip solution stubs
            if presence.get("block_solution_engine") and presence.get("seed_reply"):
                seed = str(presence["seed_reply"]).strip()
                if seed:
                    stages.append("presence_listen")
                    self.memory.add(session, "user", q, intent="sharing")
                    self.memory.add(session, "assistant", seed, intent="support")
                    return {
                        "answer": seed,
                        "handled": True,
                        "needs_model": False,
                        "stages": stages,
                        "meta": meta,
                        "intent": presence.get("intent") or {"intent": "sharing"},
                        "human_presence": presence,
                        "source": "human_presence",
                    }
            # Action needing permission — ask first
            if presence.get("requires_permission") and presence.get("permission_prompt"):
                prompt = str(presence["permission_prompt"]).strip()
                stages.append("presence_permission")
                self.memory.add(session, "user", q, intent="action")
                self.memory.add(session, "assistant", prompt, intent="permission")
                return {
                    "answer": prompt,
                    "handled": True,
                    "needs_model": False,
                    "stages": stages,
                    "meta": meta,
                    "intent": presence.get("intent") or {"intent": "action"},
                    "human_presence": presence,
                    "source": "human_presence_permission",
                }
        except Exception as exc:
            meta["human_presence"] = {"error": str(exc)}

        # 1) Understand
        stages.append("understand")
        intent = self.intent.understand(q, history=history)
        meta["intent"] = intent.to_dict()

        prefs = self.preferences.update_from_message(user_key, q)
        meta["preferences"] = prefs

        # 2) Remember
        stages.append("remember")
        mem_history = history if history is not None else self.memory.history(session)
        self.memory.add(session, "user", q, intent=intent.intent)
        ctx = self.context.build(
            q,
            history=mem_history,
            preferences=prefs,
            extra=extra,
        )
        meta["context"] = {
            "followup": ctx.get("followup"),
            "history_count": ctx.get("history_count"),
        }

        # Fast social path — never send greetings / user-name to templates
        stages.append("conversation")
        user_name = ""
        try:
            extra_d = dict(extra or {})
            user_name = str(
                extra_d.get("user_name")
                or (extra_d.get("user_context") or {}).get("name")
                or prefs.get("name")
                or prefs.get("display_name")
                or ""
            ).strip()
        except Exception:
            user_name = ""
        extra_d = dict(extra or {})
        voice_mode = bool(extra_d.get("voice_mode") or extra_d.get("skip_canned_social"))
        social = self.conversation.process(
            q,
            history=mem_history,
            user_name=user_name,
            voice_mode=voice_mode,
            skip_canned=voice_mode,
        )
        if social.get("handled") and social.get("response") and not (
            voice_mode and str((social.get("intent") or {}).get("intent") or "")
            not in {"user_name", "user_name_set"}
        ):
            answer = self.personality.wrap(
                str(social["response"]), intent=intent.intent
            )
            if social.get("remember_name"):
                try:
                    self.preferences.set(
                        user_key,
                        name=str(social["remember_name"]),
                        display_name=str(social["remember_name"]),
                    )
                except Exception:
                    pass
            safe = self.safety.filter(answer)
            answer = safe["answer"]
            self.memory.add(session, "assistant", answer, intent=intent.intent)
            conf = self.confidence.score(intent=intent.intent, quality={"score": 0.95})
            qual = self.quality.evaluate(
                answer,
                optimizer_report={"score": 0.95, "issues": []},
                confidence=conf,
                intent=intent.intent,
            )
            stages.extend(["quality", "response"])
            return {
                "answer": answer,
                "handled": True,
                "needs_model": False,
                "stages": stages,
                "meta": {
                    **meta,
                    "strategy": intent.strategy,
                    "social": True,
                    "confidence": conf,
                    "quality": qual,
                    "safety": safe.get("flags") or [],
                    "remember_name": social.get("remember_name"),
                },
                "intent": intent.to_dict(),
                "plan": {
                    "strategy": intent.strategy,
                    "steps": ["acknowledge", "personal"],
                },
                "solution": {},
                "context_blob": ctx.get("context_blob") or "",
                "system_hint": self.personality.system_hint(
                    tone=str(prefs.get("tone") or "friendly"),
                    detail=str(prefs.get("detail") or "balanced"),
                ),
            }

        # 3) Plan
        stages.append("plan")
        plan = self.planner.plan(q, intent, context=ctx)
        meta["plan"] = {
            "strategy": plan.get("strategy"),
            "style": plan.get("style"),
            "steps": plan.get("steps"),
            "ask_details": plan.get("ask_details"),
        }

        # 4) Solve — only for real problem intents (never for casual chat)
        stages.append("solve")
        solve_intents = {
            "debugging",
            "coding",
            "howto",
            "comparison",
            "explanation",
            "design",
            "problem",
            "technical",
        }
        should_solve = intent.intent in solve_intents or str(plan.get("strategy") or "") in {
            "technical_solution",
            "code_solution",
            "step_by_step",
            "comparison",
            "explanation",
        }
        solution: dict[str, Any] = {}
        if should_solve:
            solution = self.solutions.solve(
                q, plan=plan, context=ctx, model_generate=model_generate
            )
        meta["solution"] = {
            "solved": bool(solution.get("solved")),
            "kind": solution.get("kind"),
            "complete": solution.get("complete"),
            "skipped": not should_solve,
        }

        # 5) Generate (prefer full model brain whenever available)
        stages.append("generate")
        model_answer = ""
        used_model = False
        want_model = bool(
            model_generate is not None
            and (intent.needs_model or voice_mode or not solution.get("solved") or not should_solve)
        )
        if model_generate is not None and want_model:
            try:
                hint = self.personality.system_hint(
                    tone=str(prefs.get("tone") or "friendly"),
                    detail=str(prefs.get("detail") or "balanced"),
                )
                guidance = str(plan.get("guidance") or "")
                prompt_ctx = "\n".join(
                    p
                    for p in (
                        hint,
                        guidance,
                        str(ctx.get("context_blob") or ""),
                        (model_context or "")[:2000],
                        str(solution.get("answer") or "")[:1500] if solution.get("solved") else "",
                    )
                    if p
                ).strip()
                if _supports_kw(model_generate, "context"):
                    model_answer = str(
                        model_generate(q, context=prompt_ctx) or ""
                    ).strip()
                else:
                    model_answer = str(model_generate(q) or "").strip()
                used_model = bool(model_answer)
            except TypeError:
                try:
                    model_answer = str(model_generate(q) or "").strip()
                    used_model = bool(model_answer)
                except Exception as exc:
                    meta["generate_error"] = str(exc)
            except Exception as exc:
                meta["generate_error"] = str(exc)

        def _usable(text: str) -> str:
            t = (text or "").strip()
            if not t:
                return ""
            try:
                from .stub_detect import is_solution_stub

                if is_solution_stub(t):
                    return ""
            except Exception:
                pass
            try:
                from om_ai.core.companion_personality.voice_presence import (
                    is_garbage_spoken,
                )

                if is_garbage_spoken(t):
                    return ""
            except Exception:
                pass
            return t

        draft = _usable(model_answer)
        sol_ans = _usable(str(solution.get("answer") or "")) if solution.get("solved") else ""
        # Prefer model. Only use solution when it is a real non-stub answer.
        if not draft and sol_ans and not voice_mode:
            draft = sol_ans
        elif draft and sol_ans and intent.intent == "debugging" and not voice_mode:
            # Debugging: structured solution may win if longer and non-stub
            if len(sol_ans) > len(draft) + 40:
                draft = sol_ans

        if not draft:
            try:
                from om_ai.core.intelligence.real_answer import (
                    build_real_answer,
                    from_helpful_defaults,
                )

                draft = _usable(from_helpful_defaults(q) or "") or _usable(
                    build_real_answer(q) or ""
                )
                if draft:
                    meta["used_real_answer"] = True
            except Exception:
                pass

        # 6) Optimize
        stages.append("optimize")
        optimized = self.optimizer.optimize(
            draft,
            message=q,
            intent=intent.intent,
            fallback="" if voice_mode else sol_ans,
        )
        draft = _usable(str(optimized.get("answer") or draft)) or draft
        meta["optimize"] = optimized.get("report")

        # 7) Correct
        stages.append("correct")
        if voice_mode:
            corrected = {"corrected": False, "answer": draft, "reason": "voice_passthrough"}
        else:
            corrected = self.correction.correct(
                q,
                draft,
                solution=solution,
                intent=intent.intent,
            )
            draft = str(corrected.get("answer") or draft)
        meta["correction"] = {
            "corrected": bool(corrected.get("corrected")),
            "reason": corrected.get("reason"),
        }

        # 8) Quality + safety
        stages.append("quality")
        draft = self.personality.wrap(draft, intent=intent.intent)
        try:
            from .stub_detect import is_solution_stub

            if is_solution_stub(draft):
                draft = ""
        except Exception:
            pass
        if not draft:
            try:
                from om_ai.core.intelligence.real_answer import (
                    build_real_answer,
                    from_helpful_defaults,
                )

                draft = str(from_helpful_defaults(q) or build_real_answer(q) or "").strip()
            except Exception:
                draft = ""
        safe = self.safety.filter(draft)
        draft = safe["answer"]
        conf = self.confidence.score(
            intent=intent.intent,
            quality=optimized.get("report"),
            solution=solution,
            used_model=used_model,
            corrected=bool(corrected.get("corrected")),
        )
        qual = self.quality.evaluate(
            draft,
            optimizer_report=optimized.get("report"),
            confidence=conf,
            intent=intent.intent,
        )
        meta["confidence"] = conf
        meta["quality"] = qual
        meta["safety"] = safe.get("flags") or []
        meta["used_model"] = used_model

        stages.append("response")
        self.memory.add(session, "assistant", draft, intent=intent.intent)

        return {
            "answer": draft,
            "handled": True,
            "needs_model": bool(intent.needs_model and not used_model and not draft),
            "stages": stages,
            "meta": meta,
            "intent": intent.to_dict(),
            "plan": plan,
            "solution": solution,
            "context_blob": ctx.get("context_blob") or "",
            "system_hint": self.personality.system_hint(
                tone=str(prefs.get("tone") or "friendly"),
                detail=str(prefs.get("detail") or "balanced"),
            ),
            "status": self.status(),
        }


_ORCH: ChatOrchestrator | None = None


def run_chat_intelligence(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    tenant_id: str = "default",
    actor: str = "",
    model_generate: Callable[..., str] | None = None,
    model_context: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Module-level entry for chat_pipeline / API / brain."""
    global _ORCH
    if not _env_on("OM_CHAT_INTELLIGENCE", "1"):
        return {
            "answer": "",
            "handled": False,
            "stages": ["chat_intelligence_disabled"],
            "meta": {"step": 26, "disabled": True},
            "intent": {},
        }
    if _ORCH is None:
        _ORCH = ChatOrchestrator()
    return _ORCH.run(
        message,
        history=history,
        tenant_id=tenant_id,
        actor=actor,
        model_generate=model_generate,
        model_context=model_context,
        extra=extra,
    )
