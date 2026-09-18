"""OM Chat Intelligence Orchestrator — STEP 26 conversation brain."""
from __future__ import annotations

import logging
import os
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
                "response_optimizer": True,
                "correction_engine": True,
                "conversation_memory": True,
                "user_preference": True,
                "confidence_engine": True,
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
                "answer": "Hi — send me a message and I’ll help.",
                "handled": True,
                "stages": stages + ["empty"],
                "meta": {**meta, "empty": True},
                "intent": {"intent": "empty"},
            }

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

        # Fast social path — never send greetings to the small model
        stages.append("conversation")
        social = self.conversation.process(q, history=mem_history)
        if social.get("handled") and social.get("response"):
            answer = self.personality.wrap(
                str(social["response"]), intent=intent.intent
            )
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
                },
                "intent": intent.to_dict(),
                "plan": {
                    "strategy": intent.strategy,
                    "steps": ["acknowledge", "offer_help"],
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

        # 4) Solve
        stages.append("solve")
        solution = self.solutions.solve(q, plan=plan, context=ctx)
        meta["solution"] = {
            "solved": bool(solution.get("solved")),
            "kind": solution.get("kind"),
            "complete": solution.get("complete"),
        }

        # 5) Generate (optional native model)
        stages.append("generate")
        model_answer = ""
        used_model = False
        if model_generate is not None and intent.needs_model:
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
                        str(solution.get("answer") or "")[:1500],
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

        draft = model_answer
        if solution.get("solved") and solution.get("answer"):
            if not draft or len(draft) < 40:
                draft = str(solution["answer"])
            elif intent.intent == "debugging":
                draft = str(solution["answer"])
        if not draft:
            draft = (
                "I can help with that. "
                "Share a bit more detail (goal, error text, or stack) "
                "and I’ll give a concrete answer."
            )

        # 6) Optimize
        stages.append("optimize")
        optimized = self.optimizer.optimize(
            draft,
            message=q,
            intent=intent.intent,
            fallback=str(solution.get("answer") or ""),
        )
        draft = str(optimized.get("answer") or draft)
        meta["optimize"] = optimized.get("report")

        # 7) Correct
        stages.append("correct")
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
            "needs_model": bool(intent.needs_model),
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
