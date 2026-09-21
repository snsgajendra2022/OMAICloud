"""Human Companion Platform — Jarvis-style turn spine.

Voice → Human Understanding → Emotion/Context/Memory
  → Conversation Planner → Friend mind → Respond → Voice + Avatar
"""
from __future__ import annotations

import logging
import re
from typing import Any, Callable

from .actions import ActionSubsystem
from .avatar import AvatarRuntime
from .context import ContextManager
from .conversation import ConversationManager
from .emotion import EmotionSystem
from .friend_mind import FriendMind
from .memory import MemoryManager
from .personality import PersonalityCore
from .response import ResponseIntelligence
from .voice import VoiceSubsystem

logger = logging.getLogger(__name__)

_PLATFORM: "HumanCompanionPlatform | None" = None


class HumanCompanionPlatform:
    """Canonical OM human companion turn spine."""

    def __init__(self) -> None:
        self.conversation = ConversationManager()
        self.memory = MemoryManager()
        self.emotion = EmotionSystem()
        self.friend = FriendMind()
        self.personality = PersonalityCore()
        self.response = ResponseIntelligence()
        self.voice = VoiceSubsystem()
        self.context = ContextManager()
        self.avatar = AvatarRuntime()
        self.actions = ActionSubsystem()
        self._jarvis = None

    @property
    def jarvis(self):
        if self._jarvis is None:
            try:
                from om_ai.core.jarvis_brain import get_jarvis_brain

                self._jarvis = get_jarvis_brain()
            except Exception as exc:
                logger.debug("jarvis_brain unavailable: %s", exc)
                self._jarvis = False
        return self._jarvis if self._jarvis is not False else None

    def bind_actions(
        self,
        *,
        plan_fn: Callable[[str, dict[str, Any]], dict[str, Any] | None] | None = None,
        execute_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        looks_fn: Callable[[str], bool] | None = None,
    ) -> None:
        self.actions = ActionSubsystem(plan_fn=plan_fn, execute_fn=execute_fn, looks_fn=looks_fn)

    def configure_identity(self, *, session_key: str, user_key: str) -> None:
        self.memory.configure(user_key=user_key, session_key=session_key)
        self.conversation.state.session_id = session_key

    def turn(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        generate: Callable[..., str] | None = None,
        pre_answer: str = "",
        semantic: dict[str, Any] | None = None,
        skip_action: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        text = self.voice.noise.clean_transcript(message)
        hist = history or self.memory.short.history()
        pipeline: list[str] = ["heard"]

        is_action = (not skip_action) and self.actions.looks_like_action(text)
        meaning = dict(semantic or {})
        meaning.setdefault("requires_action", is_action)

        locale = "hi" if any(
            w in text.lower() for w in ("hai", "kya", "tum", "nahi", "baat", "ji")
        ) else "en"

        # —— Jarvis brain: human understanding + emotion + dialogue + personality ——
        pipeline.append("human_understanding")
        jarvis_pack: dict[str, Any] = {}
        mem = self.memory.recall(text)
        profile = mem.get("profile") or self.memory.profile.load()

        if self.jarvis is not None:
            try:
                jarvis_pack = self.jarvis.perceive(
                    text,
                    history=hist,
                    is_action=is_action,
                    locale=locale,
                    profile=profile,
                )
            except Exception as exc:
                logger.debug("jarvis perceive failed: %s", exc)
                jarvis_pack = {}

        # Meaning / topic (prefer jarvis human layer)
        pipeline.append("meaning")
        topic = str(
            (jarvis_pack.get("topic") if jarvis_pack else None)
            or self.conversation.topics.update(text, history=hist).get("topic")
            or "general"
        )
        follow = self.conversation.followups.analyze(
            text,
            state=self.conversation.state.to_dict(),
            topic=topic,
            last_assistant=self.conversation.state.last_assistant,
            last_user=self.conversation.state.last_user,
        )
        meaning["is_followup"] = bool(follow.get("is_followup") or follow.get("is_reference"))
        meaning["topic"] = topic
        if jarvis_pack.get("incomplete", {}).get("incomplete"):
            meaning["incomplete"] = True
            meaning["requires_clarification"] = False  # friend continues, does not scold

        # Emotion (prefer jarvis emotion intelligence)
        pipeline.append("emotion")
        emo = jarvis_pack.get("emotion") or self.emotion.analyze(text)
        # Normalize label field for legacy consumers
        if "label" not in emo and emo.get("emotion"):
            emo = {**emo, "label": emo["emotion"]}
        situation = {
            "emotion": emo.get("label") or emo.get("emotion"),
            "mood": emo.get("mood"),
            "need": emo.get("need"),
            "is_action": is_action,
            "is_followup": meaning["is_followup"],
            "topic": topic,
            "listen_first": bool(jarvis_pack.get("listen_first")),
            "wellbeing": (jarvis_pack.get("wellbeing") or {}).get("primary"),
        }

        # Memory / relationship / context
        pipeline.append("memory")
        ctx_aware = self.context.resolve(text, history=hist, topic=topic)
        relationship = (
            (jarvis_pack.get("human") or {}).get("relationship")
            or emo.get("relationship")
            or {}
        )
        convo = self.conversation.prepare(
            text,
            history=hist,
            memory_blob=str(mem.get("context_blob") or ""),
            emotion=emo,
            profile=profile,
            semantic=meaning,
            is_action=is_action,
            task=ctx_aware.get("task"),
        )
        policy = convo.get("policy") or {}
        enriched = str(convo.get("enriched_message") or text)

        # Conversation planner + friend mind
        pipeline.append("conversation_planner")
        dialogue = jarvis_pack.get("dialogue") or {}
        friend = self.friend.think(
            text,
            meaning={**meaning, **follow, **(jarvis_pack.get("human") or {})},
            emotion=emo,
            memory=mem,
            relationship=relationship,
            topic=topic,
            locale=locale,
        )
        # Prefer jarvis dialogue / incomplete / wellbeing asks
        if jarvis_pack.get("natural_ask"):
            friend["optional_ask"] = jarvis_pack["natural_ask"]
            if jarvis_pack.get("listen_first"):
                friend["friend_move"] = "validate_then_one_step"
                friend["stance"] = "support"
        if jarvis_pack.get("friend_move"):
            friend.setdefault("friend_move", jarvis_pack["friend_move"])
        if jarvis_pack.get("system_hint"):
            friend["system_hint"] = " ".join(
                p for p in (friend.get("system_hint"), jarvis_pack.get("system_hint")) if p
            )

        pipeline.append("personality")
        person = self.personality.prepare(
            text,
            emotion=emo,
            profile=profile,
            policy=policy,
            relationship=relationship,
        )
        jarvis_person = jarvis_pack.get("personality") or {}
        person_hint = "\n".join(
            p
            for p in (
                str(person.get("system_hint") or ""),
                str(jarvis_person.get("system_hint") or ""),
                str(friend.get("system_hint") or ""),
                str(dialogue.get("system_hint") or ""),
            )
            if p
        )

        action_result = None
        planned = None
        if is_action:
            pipeline.append("action_plan")
            planned = self.actions.plan(text, meaning)

        # Respond — seed from jarvis human layer when listening / incomplete / wellbeing
        pipeline.append("respond")
        seed = (pre_answer or "").strip()
        jarvis_seed = str(jarvis_pack.get("answer_seed") or jarvis_pack.get("answer") or "").strip()
        if jarvis_pack.get("listen_first") or (jarvis_pack.get("incomplete") or {}).get("incomplete"):
            if jarvis_seed and (not seed or len(seed.split()) < 5):
                seed = jarvis_seed
        if not seed and jarvis_pack.get("natural_ask"):
            seed = str(jarvis_pack["natural_ask"])
        if not seed and (jarvis_pack.get("incomplete") or {}).get("friend_continue"):
            seed = str(jarvis_pack["incomplete"]["friend_continue"])

        gen_out = self.response.run(
            enriched,
            generate=generate,
            context_blob=str((convo.get("context") or {}).get("context_blob") or ""),
            history=hist,
            policy={
                **policy,
                "friend_move": friend.get("friend_move"),
                "dialogue_mode": dialogue.get("mode"),
                "need": emo.get("need"),
            },
            personality_hint=person_hint,
            pre_answer=seed,
        )
        answer = str(gen_out.get("answer") or seed or "").strip()
        answer = self.personality.finalize(
            answer, user_message=text, pack={**person, "friend": friend, "jarvis": jarvis_pack}
        )

        ask = friend.get("optional_ask") or jarvis_pack.get("natural_ask")
        move = str(friend.get("friend_move") or "")
        if ask and "?" not in answer and move in {
            "one_gentle_question",
            "validate_then_one_step",
        }:
            # If answer is already the care line, keep it; else soft-append
            if ask not in answer:
                answer = f"{answer.rstrip('.')}... {ask}" if answer else str(ask)

        real_words = re.findall(r"[A-Za-z\u0900-\u097F']+", answer or "")
        if len(real_words) < 5:
            # Prefer jarvis natural ask before generic rescue
            if jarvis_pack.get("natural_ask"):
                answer = str(jarvis_pack["natural_ask"])
            else:
                try:
                    from om_ai.core.companion_personality.voice_presence import (
                        is_garbage_spoken,
                        rescue_spoken,
                    )

                    if is_garbage_spoken(answer) or len(real_words) < 5:
                        rescued = rescue_spoken(text, answer)
                        if rescued and len(re.findall(r"[A-Za-z\u0900-\u097F']+", rescued)) >= 5:
                            answer = rescued
                except Exception:
                    pass

        pipeline.append("voice_expression")
        tts_emo = str(
            emo.get("tone")
            or (emo.get("response_guide") or {}).get("tts_emotion")
            or "calm"
        )
        if emo.get("need") == "listen_first" or friend.get("friend_move") in {
            "be_more_human",
            "validate_then_one_step",
        }:
            tts_emo = "soft"
        delivery = self.voice.prepare_delivery(answer, emotion=tts_emo)
        spoken = str(delivery.get("spoken") or answer)
        spoken_tts = str(delivery.get("spoken_tts") or spoken)
        avatar = self.avatar.build(
            speaking=True,
            emotion=str(emo.get("label") or emo.get("emotion") or "neutral"),
            presence="attentive",
            spoken=spoken,
        )

        if persist:
            self.memory.remember_turn(text, spoken)
            if self.jarvis is not None:
                try:
                    self.jarvis.remember(text, spoken, topic=topic)
                except Exception:
                    pass
        self.conversation.commit(text, spoken)

        feeling = str(emo.get("label") or emo.get("emotion") or "neutral")
        mem_line = ""
        if profile.get("name"):
            mem_line = f"With {profile['name']}"
        elif topic != "general":
            mem_line = topic.replace("_", " ")
        elif ctx_aware.get("summary"):
            mem_line = str(ctx_aware["summary"])[:80]

        return {
            "answer": spoken,
            "spoken": spoken,
            "spoken_tts": spoken_tts,
            "feeling": feeling,
            "affect": {
                "label": feeling,
                "confidence": emo.get("confidence"),
                "mood": emo.get("mood"),
                "need": emo.get("need"),
                "response_style": emo.get("response_style"),
                "relationship": relationship,
            },
            "emotion": emo,
            "situation": situation,
            "friend": friend,
            "personality": person,
            "conversation": convo,
            "jarvis": {
                "human": jarvis_pack.get("human"),
                "dialogue": dialogue,
                "wellbeing": jarvis_pack.get("wellbeing"),
                "pipeline": jarvis_pack.get("pipeline"),
            },
            "wellbeing": jarvis_pack.get("wellbeing"),
            "human_context": jarvis_pack.get("human"),
            "dialogue_plan": dialogue,
            "memory": {
                "line": mem_line,
                "recall": bool(mem.get("context_blob")),
                "profile": profile,
            },
            "memory_line": mem_line,
            "context": ctx_aware,
            "meaning": meaning,
            "response_iq": {k: gen_out.get(k) for k in ("plan", "strategy", "quality", "evaluation")},
            "voice_plan": delivery,
            "avatar": avatar,
            "action_planned": planned,
            "action_result": action_result,
            "activities": [
                {
                    "heard": "Heard you",
                    "human_understanding": "Understood unspoken context",
                    "meaning": "Understood meaning",
                    "emotion": "Read emotion + situation",
                    "memory": "Recalled relationship / context",
                    "conversation_planner": "Planned conversation move",
                    "personality": "Shaped friend personality",
                    "action_plan": "Planned action",
                    "respond": "Composed natural reply",
                    "voice_expression": "Voice + expression",
                }.get(step, step)
                for step in pipeline
            ],
            "pipeline": pipeline,
            "semantic": meaning,
            "policy": policy,
            "handled": True,
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "architecture": "om_jarvis_brain",
            "pipeline": [
                "voice_input",
                "human_understanding",
                "emotion",
                "context_memory",
                "conversation_planner",
                "reasoning",
                "action_tools",
                "response_personality",
                "voice_avatar",
            ],
            "systems": {
                "human_intelligence": True,
                "emotion_intelligence": True,
                "dialogue_intelligence": True,
                "personality": True,
                "wellbeing": True,
                "jarvis_brain": self.jarvis is not None,
                "conversation": True,
                "memory": True,
                "friend_mind": True,
                "response_intelligence": True,
                "voice": True,
                "avatar": True,
                "actions": True,
            },
        }


def get_human_companion() -> HumanCompanionPlatform:
    global _PLATFORM
    if _PLATFORM is None:
        _PLATFORM = HumanCompanionPlatform()
    return _PLATFORM
