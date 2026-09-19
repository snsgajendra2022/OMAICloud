"""STEP 60 — OM Companion Operating System orchestrator.

Wires presence, continuous conversation, voice engine, avatar, human memory,
self-improvement, autonomous agent, vision, and background brain into one turn.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_OS: CompanionOS | None = None


class CompanionOS:
    """Top-level companion OS — Human Interaction → Conscious Runtime → Action → Presence."""

    def __init__(self) -> None:
        self.presence = None
        self.conversation = None
        self.voice_engine = None
        self.avatar = None
        self.human_memory = None
        self.self_improve = None
        self.autonomous = None
        self.vision = None
        self.background = None
        self.human_conversation = None
        self.language = None
        self.consciousness = None
        self.human_dialogue = None
        self.personality = None
        self.action_engine = None
        self.live_presence = None
        self.om_avatar = None
        self.neural_voice = None
        self._boot()

    def _boot(self) -> None:
        try:
            from om_ai.core.om_consciousness import get_consciousness
            self.consciousness = get_consciousness()
        except Exception as exc:
            logger.debug("consciousness: %s", exc)
        try:
            from om_ai.core.human_dialogue import get_human_dialogue
            self.human_dialogue = get_human_dialogue()
        except Exception as exc:
            logger.debug("human_dialogue: %s", exc)
        try:
            from om_ai.core.personality import get_personality
            self.personality = get_personality()
        except Exception as exc:
            logger.debug("personality: %s", exc)
        try:
            from om_ai.core.action_engine import get_action_engine
            self.action_engine = get_action_engine()
        except Exception as exc:
            logger.debug("action_engine: %s", exc)
        try:
            from om_ai.core.live_presence import get_event_bus
            self.live_presence = get_event_bus()
        except Exception as exc:
            logger.debug("live_presence: %s", exc)
        try:
            from om_ai.om_avatar import get_om_avatar
            self.om_avatar = get_om_avatar()
        except Exception as exc:
            logger.debug("om_avatar: %s", exc)
        try:
            from om_ai.core.neural_voice import get_neural_voice
            self.neural_voice = get_neural_voice()
        except Exception as exc:
            logger.debug("neural_voice: %s", exc)
        try:
            from om_ai.core.presence_engine import get_presence_runtime
            self.presence = get_presence_runtime()
        except Exception as exc:
            logger.debug("presence: %s", exc)
        try:
            from om_ai.core.conversation_runtime import get_conversation_runtime
            self.conversation = get_conversation_runtime()
        except Exception as exc:
            logger.debug("conversation: %s", exc)
        try:
            from om_ai.core.voice_engine import get_voice_engine
            self.voice_engine = get_voice_engine()
        except Exception as exc:
            logger.debug("voice_engine: %s", exc)
        try:
            from om_ai.avatar import get_avatar_engine
            self.avatar = get_avatar_engine()
        except Exception as exc:
            logger.debug("avatar: %s", exc)
        try:
            from om_ai.core.human_memory import get_human_memory
            self.human_memory = get_human_memory()
        except Exception as exc:
            logger.debug("human_memory: %s", exc)
        try:
            from om_ai.core.self_improvement import get_self_improvement
            self.self_improve = get_self_improvement()
        except Exception as exc:
            logger.debug("self_improve: %s", exc)
        try:
            from om_ai.core.autonomous_agent import get_autonomous_agent
            self.autonomous = get_autonomous_agent()
        except Exception as exc:
            logger.debug("autonomous: %s", exc)
        try:
            from om_ai.core.vision import get_vision_runtime
            self.vision = get_vision_runtime()
        except Exception as exc:
            logger.debug("vision: %s", exc)
        try:
            from om_ai.core.background_brain import get_background_brain
            self.background = get_background_brain()
        except Exception as exc:
            logger.debug("background: %s", exc)
        try:
            from om_ai.core.human_conversation import get_human_conversation
            self.human_conversation = get_human_conversation()
        except Exception as exc:
            logger.debug("human_conversation: %s", exc)
        try:
            from om_ai.core.language_intelligence import get_language_intelligence
            self.language = get_language_intelligence()
        except Exception as exc:
            logger.debug("language: %s", exc)

    def status(self) -> dict[str, Any]:
        layers = {
            "consciousness": getattr(self.consciousness, "status", lambda: {})(),
            "presence": getattr(self.presence, "status", lambda: {})(),
            "conversation": getattr(self.conversation, "status", lambda: {})(),
            "human_dialogue": getattr(self.human_dialogue, "status", lambda: {})(),
            "personality": getattr(self.personality, "status", lambda: {})(),
            "voice_engine": getattr(self.voice_engine, "status", lambda: {})(),
            "neural_voice": getattr(self.neural_voice, "status", lambda: {})(),
            "avatar": getattr(self.avatar, "status", lambda: {})(),
            "om_avatar": getattr(self.om_avatar, "status", lambda: {})(),
            "human_memory": getattr(self.human_memory, "status", lambda: {})(),
            "self_improvement": getattr(self.self_improve, "status", lambda: {})(),
            "autonomous_agent": getattr(self.autonomous, "status", lambda: {})(),
            "action_engine": getattr(self.action_engine, "status", lambda: {})(),
            "vision": getattr(self.vision, "status", lambda: {})(),
            "background_brain": getattr(self.background, "status", lambda: {})(),
            "human_conversation": getattr(self.human_conversation, "status", lambda: {})(),
            "language_intelligence": getattr(self.language, "status", lambda: {})(),
            "live_presence": {"ready": self.live_presence is not None, "step": 110},
        }
        return {
            "ready": True,
            "step": 112,
            "name": "OM Jarvis Companion OS",
            "architecture": [
                "Human Presence",
                "Consciousness Runtime",
                "Conversation + Personality",
                "Memory + Vision + Voice",
                "Action + Autonomy",
                "Live Presence + Desktop",
            ],
            "layers": layers,
        }

    def enrich_turn(
        self,
        user_text: str,
        *,
        answer: str = "",
        speaking: bool = False,
        affect: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run OS layers around a brain answer — presence, convo flow, memory, learning, avatar."""
        out: dict[str, Any] = {"os_step": 112}
        presence_pack = {}
        react_mode = ""
        consciousness_owned = False

        # STEP 100 — Consciousness owns diagnose / plan / greeting turns
        if self.consciousness:
            try:
                mind = self.consciousness.process(user_text, answer=answer, affect=affect)
                out["consciousness"] = {
                    "intention": mind.get("intention"),
                    "goal": mind.get("goal"),
                    "decision": mind.get("decision"),
                    "activity": mind.get("activity"),
                    "thoughts": mind.get("thoughts"),
                }
                out["activity"] = mind.get("activity") or []
                route = str(((mind.get("decision") or {}).get("route") or ""))
                if mind.get("answer") and route in {
                    "action_engine",
                    "personality",
                    "vision",
                }:
                    answer = str(mind["answer"])
                    consciousness_owned = True
                if mind.get("action"):
                    out["action"] = mind["action"]
                # brain / human_dialogue routes leave the companion brain answer intact
            except Exception as exc:
                logger.debug("consciousness process: %s", exc)

        # Language intelligence first (Hinglish semantic)
        locale = "en"
        language_owned = False
        human_owned = False
        if self.language and not consciousness_owned:
            lang = self.language.understand(user_text)
            out["language"] = lang
            locale = str(lang.get("locale") or "en")
            # Reminder / goal intents get structured handling — never overwrite later
            if lang.get("intent") == "create_reminder" and lang.get("confidence", 0) >= 0.7:
                slots = lang.get("slots") or {}
                when_raw = str(slots.get("when") or "")
                if locale == "hi":
                    when = {"tomorrow": "kal", "unspecified": "baad mein"}.get(when_raw, when_raw or "kal")
                else:
                    when = when_raw or "later"
                task = slots.get("task", user_text)
                if locale == "hi":
                    answer = (
                        f"Theek hai Sir — maine note kar liya. "
                        f"{when} ke liye yaad: {task}. Aur kuch?"
                    )
                else:
                    answer = (
                        f"Understood, Sir. Reminder set for {when}: {task}. Anything else?"
                    )
                language_owned = True
                try:
                    from om_ai.core.background_brain import get_background_brain
                    get_background_brain().reminders.add(str(task or user_text))
                except Exception:
                    pass

        # Human dialogue / conversation — annotate only; do NOT replace brain answers
        # with canned keyword replies (production voice path owns that via LLM + voice presence).
        if not language_owned and not consciousness_owned:
            if self.human_dialogue:
                hd = self.human_dialogue.respond(user_text, locale=locale, speaking=speaking)
                out["human_dialogue"] = hd
                # Keep emotion/intent signals — answer stays from brain / consciousness
            elif self.human_conversation:
                human = self.human_conversation.respond(user_text, locale=locale)
                out["human_conversation"] = human


        if self.presence:
            presence_pack = self.presence.react(user_text, affect=affect or {})
            react_mode = str(((presence_pack.get("presence") or {}).get("mode") or ""))
            out["presence"] = presence_pack

        conv_user = {}
        if self.conversation:
            conv_user = self.conversation.on_user(user_text, speaking=speaking)
            out["conversation"] = {"user": conv_user}
            mode = react_mode or str(((presence_pack.get("presence") or {}).get("mode") or ""))
            # Presence-led rescue only for empty / robotic catch-alls — never crush
            # intentional short Jarvis human replies or language-owned answers.
            if mode == "attentive" and not language_owned and not human_owned and not consciousness_owned:
                plain = re.sub(r"\[\[slnc[^\]]*\]\]", " ", (answer or ""), flags=re.I).lower()
                plain = " ".join(plain.split())
                weak = (
                    not plain
                    or "tell me what you need" in plain
                    or "i'm with you" in plain
                    or "i am with you" in plain
                    or "i'll handle it" in plain
                    or plain in {"ok", "okay", "sure", "done"}
                )
                if weak:
                    answer = "Tell me what happened. I am listening, Sir."
            if answer:
                asst = self.conversation.on_assistant(
                    answer,
                    user_text=user_text,
                    presence_mode=mode or "speaking",
                )
                answer = str(asst.get("answer") or answer)
                out["conversation"]["assistant"] = asst

        # Vision intent
        low = (user_text or "").lower()
        if self.vision and any(k in low for k in ("on my screen", "what do you see", "screen pe", "देख")):
            vision = self.vision.what_is_on_screen()
            out["vision"] = vision
            if not answer:
                answer = (
                    "I cannot access the screen yet without permission, Sir. "
                    "Enable screen vision and I will describe what you are looking at."
                )

        # Autonomous goal plan (plan-only unless actions wired)
        if self.autonomous and any(
            k in low for k in ("continue my", "open vs code", "open vscode", "fix the", "want to continue")
        ):
            out["autonomous"] = self.autonomous.run(user_text, execute=False)

        if self.human_memory:
            mem = self.human_memory.observe_turn(user_text, answer, affect=affect)
            out["human_memory"] = mem
            # Prefer detail style hint into meta
            if mem.get("preferences", {}).get("detail") == "detailed" and answer and len(answer) < 40:
                pass

        if self.self_improve and answer:
            out["learning"] = self.self_improve.evaluate(user_text, answer)

        presence_mode = react_mode or str(((out.get("presence") or {}).get("presence") or {}).get("mode") or "speaking")
        mood = str(((out.get("presence") or {}).get("mood") or {}).get("label") or "neutral")
        if self.om_avatar:
            out["om_avatar"] = self.om_avatar.update(
                presence=presence_mode,
                mood=mood,
                speaking=bool(answer),
                text=answer,
            )
        elif self.avatar:
            out["avatar"] = self.avatar.update(presence=presence_mode, text=answer, mood=mood)

        if answer and (self.neural_voice or self.voice_engine):
            emotion = "concerned" if presence_mode in {"concerned", "attentive"} else "calm"
            if presence_mode == "excited":
                emotion = "excited"
            voice = self.neural_voice or self.voice_engine
            out["voice_plan"] = voice.speak_plan(
                answer,
                emotion=emotion,
                **(
                    {"presence": presence_mode if presence_mode != "attentive" else "concerned"}
                    if self.voice_engine and voice is self.voice_engine
                    else {}
                ),
            )
            answer = str((out["voice_plan"] or {}).get("text") or answer)

        if self.live_presence and answer:
            try:
                self.live_presence.emit("reply_ready", {"preview": (answer or "")[:160]})
            except Exception:
                pass

        # Mark speaking only after content is finalized (keep react_mode for API presence)
        if self.presence and answer:
            speak_pack = self.presence.speaking()
            out["presence_speaking"] = speak_pack
            # Keep user-facing presence as the emotional react mode
            if react_mode:
                out["presence"] = presence_pack

        if self.background:
            focus = ""
            try:
                focus = str(
                    ((out.get("human_memory") or {}).get("projects") or {})
                    .get("projects", {})
                    .get("OM", {})
                    .get("last_focus")
                    or ""
                )
            except Exception:
                focus = ""
            out["background"] = self.background.tick(
                last_focus=focus,
                topic=str(((out.get("conversation") or {}).get("user") or {}).get("topic") or ""),
            )

        out["answer"] = answer
        out["spoken"] = answer
        return out


def get_companion_os() -> CompanionOS:
    global _OS
    if _OS is None:
        _OS = CompanionOS()
    return _OS
