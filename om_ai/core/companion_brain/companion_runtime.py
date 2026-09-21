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
                "answer": rescue_spoken(q),
                "spoken": rescue_spoken(q),
                "spoken_tts": rescue_spoken(q),
                "heard": q,
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

        # Voice presence prepares the brain (language + emotion + personality prompt)
        # — it does NOT invent canned replies.
        from om_ai.core.companion_personality.voice_presence import (
            get_voice_presence,
            shape_for_speech,
            is_garbage_spoken,
            rescue_spoken,
            detect_speech_locale,
        )

        vp = get_voice_presence()
        locale = detect_speech_locale(q)
        emotion = vp.emotion.detect(q)
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
        meta["voice_presence"] = {"locale": locale, "emotion": emotion}

        activities.append(_PUBLIC_ACTIVITIES["remember"])
        recall = self.memory.recall(
            q,
            session_key=session.session_key,
            user_key=session.user_key,
            project_key=session.project_id,
        )
        prefs = recall.get("preferences") or {}
        # Long-term human_memory blob (episodic / emotional / projects)
        hm_blob = str((extra or {}).get("human_memory_blob") or "").strip()
        if not hm_blob:
            try:
                from om_ai.core.human_memory import get_human_memory

                hm_blob = str(get_human_memory().recall_blob() or "").strip()
            except Exception:
                hm_blob = ""
        mem_blob = "\n".join(
            p
            for p in (
                str(recall.get("context_blob") or "").strip(),
                hm_blob[:1200] if hm_blob else "",
            )
            if p
        )
        human_ctx = self.human.build(
            message=q,
            history=hist,
            memory_blob=mem_blob,
            preferences=prefs,
        )

        personality_pack = self.affect.build(
            q, semantic, history=hist, preferences=prefs
        )
        meta["personality"] = {
            "affect": personality_pack.get("affect"),
            "expression": personality_pack.get("expression"),
            "tone": personality_pack.get("tone"),
            "relationship": personality_pack.get("relationship"),
        }

        policy = self.policy.decide(semantic)
        # STEP 51–56 — Human Conversation Pipeline before LLM
        human_layer: dict[str, Any] = {}
        try:
            from om_ai.core.jarvis_brain import get_jarvis_brain

            human_layer = get_jarvis_brain().perceive(
                q,
                history=hist,
                is_action=bool(semantic.get("requires_action")),
                locale=locale,
                profile={"name": str(((extra or {}).get("user_context") or {}).get("name") or "")},
                memory_blob=str(human_ctx.get("context_blob") or ""),
            )
            meta["human_layer"] = {
                "intent": human_layer.get("intent"),
                "emotion": (
                    (human_layer.get("emotion") or {}).get("emotion")
                    if isinstance(human_layer.get("emotion"), dict)
                    else human_layer.get("emotion")
                ),
                "need": human_layer.get("need")
                or (
                    (human_layer.get("emotion") or {}).get("need")
                    if isinstance(human_layer.get("emotion"), dict)
                    else None
                ),
                "stages": human_layer.get("stages"),
            }
            meta["wellbeing"] = human_layer.get("wellbeing")
        except Exception:
            human_layer = {}

        # Friend mind — what a loyal companion would do next
        friend_pack: dict[str, Any] = {}
        try:
            from om_ai.core.human_companion.friend_mind import FriendMind

            topic = str(
                human_layer.get("topic")
                or semantic.get("domain")
                or semantic.get("conversation_mode")
                or "general"
            )
            emo_for_friend = human_layer.get("emotion") if isinstance(human_layer.get("emotion"), dict) else {
                "label": emotion if isinstance(emotion, str) else (emotion or {})
            }
            friend_pack = FriendMind().think(
                q,
                meaning={**semantic, **(human_layer.get("human") or {})},
                emotion=emo_for_friend,
                memory={"profile": {"name": str(((extra or {}).get("user_context") or {}).get("name") or "")}},
                relationship=(personality_pack.get("relationship") if isinstance(personality_pack, dict) else {}) or {},
                topic=topic,
                locale=locale,
            )
            if human_layer.get("natural_ask"):
                friend_pack["optional_ask"] = human_layer["natural_ask"]
            if human_layer.get("system_hint"):
                friend_pack["system_hint"] = " ".join(
                    p for p in (friend_pack.get("system_hint"), human_layer.get("system_hint")) if p
                )
            meta["friend"] = friend_pack
        except Exception:
            friend_pack = {}

        emo_label = ""
        if isinstance(human_layer.get("emotion"), dict):
            emo_label = str(human_layer["emotion"].get("emotion") or human_layer["emotion"].get("label") or "")
        elif human_layer.get("emotion"):
            emo_label = str(human_layer.get("emotion"))
        if not emo_label:
            emo_label = emotion if isinstance(emotion, str) else str((emotion or {}).get("label") or "neutral")

        strat = self.strategy.select(
            semantic,
            policy,
            emotion={"label": emo_label, "need": human_layer.get("need")},
            friend=friend_pack,
        )
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
            vp.system_prompt(
                {
                    "conversation_mode": str(semantic.get("conversation_mode") or "assist"),
                    "locale": locale,
                    "emotion": emotion,
                    "user_message": q,
                    "purpose": str(((extra or {}).get("user_context") or {}).get("purpose") or ""),
                    "topic": str(semantic.get("domain") or ""),
                    "policy": policy,
                    "system_hint": str(friend_pack.get("system_hint") or ""),
                }
            ),
            str(personality_pack.get("system_hint") or ""),
            str(friend_pack.get("system_hint") or ""),
            str(human_layer.get("system_hint") or ""),
            str(human_ctx.get("context_blob") or ""),
            str(knowledge.get("blob") or ""),
            str(reasoning.get("hint") or ""),
            str(strat.get("instruction") or ""),
            model_context or "",
            "Speak like a loyal friend. Keep it short and human. Do not append a canned follow-up question.",
            "Never say 'Please complete your sentence'. Continue partial thoughts naturally.",
            "Use remembered facts (name, preferences, recent turns) naturally when relevant.",
        ]
        merged_context = "\n".join(p for p in ctx_parts if p).strip()[:4000]

        activities.append(_PUBLIC_ACTIVITIES["respond"])
        # Prefer human-layer seed for listen/support/incomplete turns
        seed = ""
        if human_layer.get("listen_first") or (human_layer.get("incomplete") or {}).get("incomplete"):
            seed = str(human_layer.get("answer_seed") or human_layer.get("natural_ask") or "").strip()

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
                "voice_mode": True,
                "skip_canned_social": True,
                "pre_answer": seed,
            },
        )
        answer = str(gen.get("answer") or seed or "").strip()
        answer = self.personality.finalize(
            answer,
            personality_pack,
            conversation_mode=str(semantic.get("conversation_mode") or "assist"),
            user_message=q,
            voice_mode=True,
        )
        if not answer or is_garbage_spoken(answer):
            answer = rescue_spoken(q, answer)
        voice_pack = shape_for_speech(answer, user_message=q)
        answer = str(voice_pack.get("spoken") or answer)

        affect = (personality_pack.get("affect") or {}) if isinstance(personality_pack, dict) else {}
        expression = personality_pack.get("expression") if isinstance(personality_pack, dict) else None

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
        if not is_garbage_spoken(answer):
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
            "spoken": answer,
            "spoken_tts": voice_pack.get("spoken_tts") or answer,
            "heard": q,
            "handled": True,
            "activities": activities,
            "semantic": semantic,
            "intent": intent.to_dict(),
            "feeling": affect.get("label") or "neutral",
            "affect": affect,
            "friend": friend_pack,
            "pipeline": [
                "heard",
                "meaning",
                "emotion",
                "memory",
                "friend_mind",
                "respond",
                "voice_expression",
            ],
            "meta": {
                **meta,
                "interrupt": interrupt,
                "friend": friend_pack,
                "memory": {
                    "disabled": recall.get("disabled"),
                    "hits": len(recall.get("hits") or []),
                },
                "source": gen.get("source"),
                "voice_trimmed": voice_pack.get("trimmed"),
                "locale": voice_pack.get("locale"),
            },
            "plan": plan,
            "session": session.to_dict(),
            "history": updated_history,
            "expression": expression,
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
