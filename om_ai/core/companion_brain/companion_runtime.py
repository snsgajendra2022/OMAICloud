"""Companion brain turn runner."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable

from .action_planner import ActionPlanner
from .affect_context import AffectContext
from .conversation_manager import ConversationManager
from .dialogue_policy import DialoguePolicy
from .human_context import HumanContext
from .intent_engine import CompanionIntentEngine
from .interruption_context import InterruptionContext
from .knowledge_bridge import KnowledgeBridge
from .memory_bridge import MemoryBridge
from .personality_engine import PersonalityBridge
from .reasoning_bridge import ReasoningBridge
from .response_engine import ResponseEngine
from .response_strategy import ResponseStrategy
from .semantic_understanding import SemanticUnderstanding
from .turn_manager import TurnManager

logger = logging.getLogger(__name__)

_PUBLIC_ACTIVITIES = {
    "companion": "Companion ready",
    "understand": "Getting the gist",
    "remember": "Recalling context",
    "plan": "Choosing approach",
    "respond": "Composing reply",
    "listen": "Listening",
}


def _env_on(name: str, default: str = "1") -> bool:
    return (os.getenv(name) or default).strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


class CompanionRuntime:
    """
    Companion conversation brain:

      message → semantic frame → memory/personality → plan → chat runtime → answer
    """

    def __init__(self) -> None:
        self.conversations = ConversationManager()
        self.intent_engine = CompanionIntentEngine()
        self.semantic = SemanticUnderstanding()
        self.policy = DialoguePolicy()
        self.strategy = ResponseStrategy()
        self.human = HumanContext()
        self.affect = AffectContext()
        self.personality = PersonalityBridge()
        self.memory = MemoryBridge()
        self.knowledge = KnowledgeBridge()
        self.reasoning = ReasoningBridge()
        self.planner = ActionPlanner()
        self.response = ResponseEngine()
        self.interruption = InterruptionContext()
        self.turns = TurnManager()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "name": "Companion Brain",
            "memory_disabled": self.memory.disabled,
            "activities": dict(_PUBLIC_ACTIVITIES),
        }

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        tenant_id: str = "default",
        actor: str = "",
        project_id: str = "",
        session_id: str | None = None,
        model_generate: Callable[..., str] | None = None,
        model_context: str = "",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        activities: list[str] = [_PUBLIC_ACTIVITIES["companion"]]
        meta: dict[str, Any] = {"runtime": "companion_brain"}
        q = (message or "").strip()

        session = self.conversations.open(
            tenant_id=tenant_id,
            actor=actor,
            project_id=project_id,
            session_id=session_id,
        )
        interrupt = self.interruption.analyze(
            q, session_interrupted=session.interrupted
        )
        session.interrupted = interrupt.get("interrupted", False)

        if not q:
            activities.append(_PUBLIC_ACTIVITIES["listen"])
            return {
                "answer": "I'm here — tell me what's on your mind.",
                "handled": True,
                "activities": activities,
                "semantic": {
                    "intent": "empty",
                    "goal": "invite",
                    "domain": "general",
                    "conversation_mode": "social",
                    "requires_memory": False,
                    "requires_model": False,
                    "requires_action": False,
                    "requires_clarification": False,
                    "confidence": 1.0,
                },
                "meta": meta,
                "session": session.to_dict(),
            }

        activities.append(_PUBLIC_ACTIVITIES["understand"])
        hist = self.conversations.history_for(session, external=history)
        intent = self.intent_engine.analyze(q, history=hist)
        human_ctx = self.human.build(message=q, history=hist)
        semantic = self.semantic.compose(
            q,
            intent,
            history=hist,
            followup=bool(human_ctx.get("followup")),
        )
        session.last_semantic = semantic
        meta["semantic"] = semantic

        activities.append(_PUBLIC_ACTIVITIES["remember"])
        recall = self.memory.recall(
            q,
            session_key=session.session_key,
            user_key=session.user_key,
            project_key=session.project_id,
        )
        prefs = recall.get("preferences") or {}
        human_ctx = self.human.build(
            message=q,
            history=hist,
            memory_blob=str(recall.get("context_blob") or ""),
            preferences=prefs,
        )

        personality_pack = self.affect.build(
            q, semantic, history=hist, preferences=prefs
        )
        meta["personality"] = {
            "affect": personality_pack.get("affect"),
            "expression": personality_pack.get("expression"),
        }

        policy = self.policy.decide(semantic)
        strat = self.strategy.select(semantic, policy)
        knowledge = self.knowledge.enrich(q, semantic=semantic)
        reasoning = self.reasoning.assist(
            q,
            semantic=semantic,
            context_blob=human_ctx.get("context_blob") or "",
        )

        activities.append(_PUBLIC_ACTIVITIES["plan"])
        plan = self.planner.plan(
            semantic,
            policy,
            strat,
            memory_recall=recall,
            knowledge=knowledge,
            reasoning=reasoning,
        )
        meta["plan"] = plan
        meta["policy"] = policy
        meta["strategy"] = strat

        ctx_parts = [
            str(personality_pack.get("system_hint") or ""),
            str(human_ctx.get("context_blob") or ""),
            str(knowledge.get("blob") or ""),
            str(reasoning.get("hint") or ""),
            model_context or "",
        ]
        merged_context = "\n".join(p for p in ctx_parts if p).strip()[:3500]

        activities.append(_PUBLIC_ACTIVITIES["respond"])
        gen = self.response.generate(
            q,
            strategy=strat,
            history=hist,
            tenant_id=tenant_id,
            actor=actor,
            model_generate=model_generate,
            model_context=merged_context,
            extra={
                **(extra or {}),
                "semantic": semantic,
                "interrupt": interrupt,
            },
        )
        answer = str(gen.get("answer") or "").strip()
        if not answer:
            answer = (
                "I want to help — could you share a bit more detail "
                "so I can give a useful answer?"
            )

        answer = self.personality.finalize(
            answer,
            personality_pack,
            conversation_mode=str(semantic.get("conversation_mode") or "assist"),
        )

        session.bump_turn()
        self.turns.record(session.session_id, "user", q, intent=intent.intent)
        self.turns.record(session.session_id, "assistant", answer, intent=intent.intent)
        self.memory.remember_turn(
            session_key=session.session_key,
            user_key=session.user_key,
            role="user",
            content=q,
            intent=intent.intent,
            project_key=session.project_id,
            confidence=float(semantic.get("confidence") or 0),
        )
        self.memory.remember_turn(
            session_key=session.session_key,
            user_key=session.user_key,
            role="assistant",
            content=answer,
            intent=intent.intent,
            project_key=session.project_id,
            confidence=float(semantic.get("confidence") or 0),
        )

        updated_history = self.turns.append_to_history(hist, "user", q)
        updated_history = self.turns.append_to_history(
            updated_history, "assistant", answer
        )

        return {
            "answer": answer,
            "handled": True,
            "activities": activities,
            "semantic": semantic,
            "intent": intent.to_dict(),
            "meta": {
                **meta,
                "interrupt": interrupt,
                "memory": {
                    "disabled": recall.get("disabled"),
                    "hits": len(recall.get("hits") or []),
                },
                "source": gen.get("source"),
            },
            "plan": plan,
            "session": session.to_dict(),
            "history": updated_history,
            "expression": personality_pack.get("expression"),
            "system_hint": personality_pack.get("system_hint"),
            "status": self.status(),
        }


_RUNTIME: CompanionRuntime | None = None


def run_companion_brain(message: str, **kwargs: Any) -> dict[str, Any]:
    global _RUNTIME
    if not _env_on("OM_COMPANION_BRAIN", "1"):
        return {
            "answer": "",
            "handled": False,
            "activities": ["Companion paused"],
            "meta": {"disabled": True},
            "semantic": {},
        }
    if _RUNTIME is None:
        _RUNTIME = CompanionRuntime()
    return _RUNTIME.run(message, **kwargs)
