"""Human Companion Platform — full 11-system turn pipeline."""
from __future__ import annotations

import logging
from typing import Any, Callable

from .actions import ActionSubsystem
from .avatar import AvatarRuntime
from .context import ContextManager
from .conversation import ConversationManager
from .emotion import EmotionSystem
from .memory import MemoryManager
from .personality import PersonalityCore
from .response import ResponseIntelligence
from .voice import VoiceSubsystem

logger = logging.getLogger(__name__)

_PLATFORM: "HumanCompanionPlatform | None" = None


class HumanCompanionPlatform:
    """
    Voice → Conversation Intelligence → (Memory · Emotion · Personality)
      → Response Intelligence → Voice delivery · Avatar · Actions
    """

    def __init__(self) -> None:
        self.conversation = ConversationManager()
        self.memory = MemoryManager()
        self.emotion = EmotionSystem()
        self.personality = PersonalityCore()
        self.response = ResponseIntelligence()
        self.voice = VoiceSubsystem()
        self.context = ContextManager()
        self.avatar = AvatarRuntime()
        self.actions = ActionSubsystem()

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
        activities = ["Companion intelligence"]

        # Emotion
        activities.append("Reading emotion")
        emo = self.emotion.analyze(text)

        # Memory recall + profile
        activities.append("Recalling memory")
        mem = self.memory.recall(text)
        profile = mem.get("profile") or self.memory.profile.load()

        # Context awareness
        ctx_aware = self.context.resolve(
            text,
            history=history or self.memory.short.history(),
            topic=self.conversation.topics.current,
        )

        is_action = (not skip_action) and self.actions.looks_like_action(text)

        # Conversation intelligence
        activities.append("Conversation continuity")
        convo = self.conversation.prepare(
            text,
            history=history or self.memory.short.history(),
            memory_blob=str(mem.get("context_blob") or ""),
            emotion=emo,
            profile=profile,
            semantic=semantic,
            is_action=is_action,
            task=ctx_aware.get("task"),
        )
        policy = convo.get("policy") or {}
        enriched = str(convo.get("enriched_message") or text)

        # Personality
        activities.append("Personality")
        person = self.personality.prepare(
            text,
            emotion=emo,
            profile=profile,
            policy=policy,
            relationship=emo.get("relationship"),
        )

        # Actions (optional — usually handled by CompanionRuntime action-first)
        action_result = None
        planned = None
        if is_action:
            activities.append("Action plan")
            planned = self.actions.plan(text, semantic or {})

        # Response intelligence
        activities.append("Response intelligence")
        gen_out = self.response.run(
            enriched,
            generate=generate,
            context_blob=str((convo.get("context") or {}).get("context_blob") or ""),
            history=history,
            policy=policy,
            personality_hint=str(person.get("system_hint") or ""),
            pre_answer=pre_answer,
        )
        answer = str(gen_out.get("answer") or pre_answer or "").strip()
        answer = self.personality.finalize(answer, user_message=text, pack=person)

        # Voice timing / natural delivery
        tts_emo = str((emo.get("response_guide") or {}).get("tts_emotion") or "calm")
        delivery = self.voice.prepare_delivery(answer, emotion=tts_emo)
        spoken = str(delivery.get("spoken") or answer)
        spoken_tts = str(delivery.get("spoken_tts") or spoken)

        # Avatar presence
        avatar = self.avatar.build(
            speaking=True,
            emotion=str(emo.get("label") or "neutral"),
            presence="attentive",
            spoken=spoken,
        )

        if persist:
            self.memory.remember_turn(text, spoken)
            self.conversation.commit(text, spoken)
        else:
            self.conversation.commit(text, spoken)

        feeling = str(emo.get("label") or "neutral")
        topic_name = str((convo.get("topic") or {}).get("topic") or "general")
        mem_line = ""
        if profile.get("name"):
            mem_line = f"With {profile['name']}"
        elif topic_name != "general":
            mem_line = topic_name.replace("_", " ")
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
                "relationship": emo.get("relationship"),
            },
            "emotion": emo,
            "personality": person,
            "conversation": convo,
            "memory": {
                "line": mem_line,
                "recall": bool(mem.get("context_blob")),
                "profile": profile,
            },
            "memory_line": mem_line,
            "context": ctx_aware,
            "response_iq": {k: gen_out.get(k) for k in ("plan", "strategy", "quality", "evaluation")},
            "voice_plan": delivery,
            "avatar": avatar,
            "action_planned": planned,
            "action_result": action_result,
            "activities": activities,
            "semantic": semantic or {},
            "policy": policy,
            "handled": True,
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "systems": {
                "conversation": True,
                "memory": True,
                "emotion": True,
                "personality": True,
                "response_intelligence": True,
                "voice": True,
                "voice_timing": True,
                "context": True,
                "avatar": True,
                "actions": True,
            },
        }


def get_human_companion() -> HumanCompanionPlatform:
    global _PLATFORM
    if _PLATFORM is None:
        _PLATFORM = HumanCompanionPlatform()
    return _PLATFORM
