"""STEP 56 — OM Human Conversation Pipeline.

message
  → human_context_engine
  → emotion_engine
  → dialogue_manager
  → memory_retrieval
  → personality_engine
  → (caller) llm
  → response_optimizer hints
  → (caller) voice_output
"""
from __future__ import annotations

import re
from typing import Any, Callable

from om_ai.core.dialogue_intelligence import DialogueManager
from om_ai.core.emotion_intelligence import EmotionEngine
from om_ai.core.human_intelligence.human_context_engine import HumanContextEngine
from om_ai.core.personality import get_personality
from om_ai.core.wellbeing_intelligence import WellbeingEngine

_PIPE: "HumanConversationPipeline | None" = None


def _is_tired(low: str) -> bool:
    return bool(re.search(r"(?i)\b(i am|i'?m|feeling)?\s*(very\s+)?tired\b|\bthak\b", low))


class HumanConversationPipeline:
    """Pre-LLM human layer + post-LLM personality shaping hints."""

    def __init__(self) -> None:
        self.context_engine = HumanContextEngine()
        self.emotion_engine = EmotionEngine()
        self.dialogue_manager = DialogueManager()
        self.personality_engine = get_personality()
        self.wellbeing_engine = WellbeingEngine()

    def run(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        memory_blob: str = "",
        profile: dict[str, Any] | None = None,
        is_action: bool = False,
        locale: str = "en",
        generate: Callable[..., str] | None = None,
        pre_answer: str = "",
    ) -> dict[str, Any]:
        hist = history or []
        profile = profile or {}

        # 1) Human context
        emo_seed = self.emotion_engine.analyze(message, history=hist)
        human = self.context_engine.understand(message, history=hist, emotion=emo_seed)

        # 2) Emotion (+ wellbeing signals)
        wellbeing = self.wellbeing_engine.observe(message, locale=locale)
        emo = self.emotion_engine.analyze(
            message,
            history=hist,
            listen_first_hint=bool(human.get("listen_first") or wellbeing.get("active")),
        )
        if wellbeing.get("active"):
            emo["need"] = "support_and_listen" if emo.get("emotion") in {
                "tired", "fatigue", "sad", "stressed", "masked_stress"
            } or wellbeing.get("signal") in {"fatigue", "sleep_deprivation"} else "listen_first"
            # Map fatigue alias
            if wellbeing.get("signal") == "fatigue":
                emo["emotion"] = "fatigue"
                emo["label"] = "fatigue"
            elif wellbeing.get("signal") == "sleep_deprivation":
                emo["emotion"] = emo.get("emotion") if emo.get("emotion") not in {"neutral"} else "tired"
                emo["label"] = emo["emotion"]
            emo["response_style"] = "supportive"
            emo["tone"] = "warm"
            emo["followup_required"] = True
            human["listen_first"] = True
            if wellbeing.get("care_line"):
                human["natural_ask"] = wellbeing["care_line"]

        # Normalize tired phrasing → fatigue pack (example in prompt)
        low = (message or "").lower()
        if _is_tired(low) and not wellbeing.get("active"):
            emo.update(
                {
                    "emotion": "fatigue",
                    "label": "fatigue",
                    "need": "support_and_listen",
                    "response_style": "supportive",
                    "tone": "warm",
                    "followup_required": True,
                    "confidence": max(float(emo.get("confidence") or 0.6), 0.8),
                }
            )
            human["listen_first"] = True
            human["natural_ask"] = (
                "You sound really tired today. "
                "Was it because of work, stress, or something else? "
                "If you have been pushing yourself too much, take a small break also."
            )

        # 3) Dialogue planner
        dialogue = self.dialogue_manager.plan(
            message,
            human=human,
            emotion=emo,
            is_action=is_action,
            locale=locale,
        )

        # 4) Memory retrieval (blob + profile already passed in)
        memory = {
            "blob": (memory_blob or "")[:2000],
            "profile": profile,
            "who": str(profile.get("name") or "user"),
            "preferences": profile.get("preferences") or {},
            "dialogue": self.context_engine.memory.to_dict(),
        }

        # 5) Personality
        person = self.personality_engine.prepare(
            message,
            emotion=emo,
            human=human,
            profile=profile,
            locale=locale,
        )

        system_hint = "\n".join(
            p
            for p in (
                "You are OM — the user's brother (bhai). Not a robot. Care first. Feel with them.",
                str(human.get("system_hint") or ""),
                str(dialogue.get("system_hint") or ""),
                str(person.get("system_hint") or ""),
                str(wellbeing.get("system_hint") or "") if wellbeing.get("active") else "",
                f"Memory:\n{memory['blob']}" if memory["blob"] else "",
            )
            if p
        )

        natural_ask = (
            human.get("natural_ask")
            or dialogue.get("followup")
            or dialogue.get("question")
        )
        if wellbeing.get("active") and wellbeing.get("care_line"):
            natural_ask = wellbeing["care_line"]

        # Intent summary for callers
        intent = "action" if is_action else "conversation"
        if (human.get("conversation") or {}).get("is_question"):
            intent = "question"
        elif (human.get("conversation") or {}).get("celebration"):
            intent = "share_win"
        elif human.get("listen_first"):
            intent = "conversation"

        # 6) Optional LLM generate
        answer = (pre_answer or "").strip()
        if not answer and natural_ask and (
            human.get("listen_first")
            or (human.get("incomplete") or {}).get("incomplete")
            or wellbeing.get("active")
        ):
            answer = str(natural_ask)
        if not answer and generate:
            try:
                answer = str(generate(message, system_hint) or "").strip()
            except TypeError:
                try:
                    answer = str(generate(message) or "").strip()
                except Exception:
                    answer = ""
            except Exception:
                answer = ""

        # Greeting / presence when nothing else seeded
        if not answer and re.search(r"(?i)^\s*(hey|hi|hello|namaste)\b.*\bom\b|\bhey\s+om\b", message or ""):
            answer = "Haan bhai, main yahan hoon." if locale == "hi" else "Hey brother — I'm right here."
        if not answer and (human.get("conversation") or {}).get("ack_only"):
            answer = "Haan bhai." if locale == "hi" else "Got you, brother."

        # 7) Response optimizer (personality polish)
        optimized = self.optimize_response(
            answer or str(natural_ask or ""),
            emotion=emo,
            human=human,
            personality=person,
            locale=locale,
        )

        stages = [
            "human_context_engine",
            "emotion_engine",
            "dialogue_manager",
            "memory_retrieval",
            "personality_engine",
            "llm" if generate or pre_answer else "seed_response",
            "response_optimizer",
        ]

        return {
            "answer": optimized,
            "spoken": optimized,
            "intent": intent,
            "emotion": emo.get("emotion") or emo.get("label"),
            "need": emo.get("need"),
            "followup_required": bool(emo.get("followup_required") or human.get("listen_first")),
            "tone": emo.get("tone") or "calm",
            "response_style": emo.get("response_style") or "balanced",
            "human": human,
            "emotion_pack": emo,
            "wellbeing": wellbeing,
            "dialogue": dialogue,
            "memory": memory,
            "personality": person,
            "natural_ask": natural_ask,
            "system_hint": system_hint,
            "listen_first": bool(human.get("listen_first")),
            "incomplete": human.get("incomplete") or {},
            "topic": human.get("topic"),
            "stages": stages,
            "pipeline": stages,
        }

    def optimize_response(
        self,
        answer: str,
        *,
        emotion: dict[str, Any] | None = None,
        human: dict[str, Any] | None = None,
        personality: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> str:
        text = (answer or "").strip()
        emotion = emotion or {}
        human = human or {}
        personality = personality or {}

        # Strip helpdesk / robotic lines
        for banned in (
            "How can I help you",
            "What can I do for you",
            "Please complete your sentence",
            "As an AI",
            "Share one more detail",
            "The bug has been fixed.",
        ):
            if banned.lower() in text.lower():
                text = text.replace(banned, "").replace(banned.lower(), "").strip()

        # Celebration friend rewrite if still robotic
        if (human.get("conversation") or {}).get("celebration") or (
            personality.get("friendship") or {}
        ).get("mode") == "celebrate":
            if len(text.split()) < 6 or "has been fixed" in text.lower():
                text = (
                    "Nice! That bug was probably annoying. What was causing the issue?"
                    if locale != "hi"
                    else "Wah! Woh bug pakka annoying tha. Asli issue kya tha?"
                )

        # Incomplete speech — never scold
        if (human.get("incomplete") or {}).get("incomplete"):
            cont = (human.get("incomplete") or {}).get("friend_continue")
            if cont and (
                "complete your sentence" in text.lower()
                or len(text.split()) < 5
            ):
                text = str(cont)

        if not text and human.get("natural_ask"):
            text = str(human["natural_ask"])
        return text.strip()

    def remember(self, user: str, assistant: str, *, topic: str = "") -> None:
        self.context_engine.remember_turn(user, assistant, topic=topic)


def get_human_conversation_pipeline() -> HumanConversationPipeline:
    global _PIPE
    if _PIPE is None:
        _PIPE = HumanConversationPipeline()
    return _PIPE
