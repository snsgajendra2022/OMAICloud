"""
Real-Time Human Conversation Intelligence — master loop.

Voice → audio → speech meaning → emotion → timing → response plan → brain.
"""
from __future__ import annotations

from typing import Any

from om_ai.core.audio_intelligence import get_listening_engine
from om_ai.core.conversation_timing import get_timing_engine
from om_ai.core.emotional_intelligence import get_emotional_intelligence
from om_ai.core.human_response import HumanResponsePlanner
from om_ai.core.speech_intelligence import MeaningReconstruction, PartialTranscript


_LOOP: HumanConversationIntelligence | None = None


class HumanConversationIntelligence:
    def __init__(self) -> None:
        self.listen = get_listening_engine()
        self.partials = PartialTranscript()
        self.meaning = MeaningReconstruction()
        self.emotion = get_emotional_intelligence()
        self.timing = get_timing_engine()
        self.responses = HumanResponsePlanner()

    def on_partial(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        rms: float = 0.0,
        speech_prob: float = 0.6,
    ) -> dict[str, Any]:
        audio = self.listen.on_audio(rms=rms, speech_prob=speech_prob)
        self.listen.on_partial_text(text)
        pt = self.partials.update(text)
        meaning = self.meaning.reconstruct(pt.get("partial") or text, history=history)
        emo = self.emotion.analyze(
            pt.get("partial") or text,
            history=history,
            voice_cues={
                "hesitation": bool((meaning.get("uncertainty") or {}).get("markers")),
                "silence_ms": float((audio.get("vad") or {}).get("silence_ms") or 0),
            },
        )
        decision = self.timing.decide(
            meaning,
            emotion=emo,
            om_speaking=bool(audio.get("om_speaking")),
            user_speaking=True,
        )
        return {
            "mode": "partial",
            "partial": pt,
            "meaning": meaning,
            "emotion": emo,
            "timing": decision,
            "audio": audio,
            "commit": False,
            "hold": bool(decision.get("should_wait") or decision.get("action") == "wait"),
        }

    def on_final(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        preferences: dict[str, Any] | None = None,
        locale: str = "en",
        force: bool = False,
        rms: float = 0.0,
        speech_prob: float = 0.75,
    ) -> dict[str, Any]:
        audio = self.listen.on_audio(rms=rms, speech_prob=speech_prob)
        self.listen.on_final_text(text)
        meaning = self.meaning.reconstruct(text, history=history)
        emo = self.emotion.analyze(
            text,
            history=history,
            voice_cues={
                "hesitation": bool((meaning.get("uncertainty") or {}).get("prefer_listen")),
                "silence_ms": float((audio.get("vad") or {}).get("silence_ms") or 0),
            },
        )
        decision = self.timing.decide(meaning, emotion=emo, om_speaking=False, user_speaking=False)

        # Incomplete final → hold (unless forced commit after silence window)
        if not force and (decision.get("should_wait") or meaning.get("needs_listening")):
            hold = self.timing.pause.begin_hold(text)
            self.partials.clear()
            return {
                "mode": "hold",
                "commit": False,
                "hold": True,
                "text": text,
                "meaning": meaning,
                "emotion": emo,
                "timing": {**decision, "hold": hold},
                "response_plan": {"speak": False, "wait": True},
                "audio": audio,
            }

        # Forced commit after natural pause — merge buffer and answer
        if force:
            ready = self.timing.pause.ready()
            if ready.get("buffer") and text:
                merged = ready["buffer"]
                if text.strip().lower() not in merged.lower():
                    text = f"{merged} {text}".strip()
                else:
                    text = merged
            elif ready.get("buffer"):
                text = str(ready["buffer"])
            meaning = self.meaning.reconstruct(text, history=history)
            emo = self.emotion.analyze(text, history=history)
            decision = self.timing.decide(meaning, emotion=emo)
            # After an explicit force commit, never stay in wait/listen
            if decision.get("action") in {"wait", "listen"} or decision.get("should_wait"):
                decision = {
                    **decision,
                    "action": "answer",
                    "move": "natural_reply",
                    "should_wait": False,
                    "should_answer": True,
                    "reason": "forced_commit",
                }

        plan = self.responses.plan(
            timing=decision,
            emotion=emo,
            meaning=meaning,
            preferences=preferences,
            locale=locale,
        )
        self.partials.clear()
        self.timing.pause.clear()
        return {
            "mode": "final",
            "commit": True,
            "hold": False,
            "text": text,
            "meaning": meaning,
            "emotion": emo,
            "timing": decision,
            "response_plan": plan,
            "system_hint": (plan.get("style") or {}).get("system_hint") or "",
            "audio": audio,
        }

    def set_om_speaking(self, speaking: bool) -> None:
        self.listen.set_om_speaking(speaking)

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "listening": self.listen.status(),
            "name": "HumanConversationIntelligence",
        }


def get_human_conversation_intelligence() -> HumanConversationIntelligence:
    global _LOOP
    if _LOOP is None:
        _LOOP = HumanConversationIntelligence()
    return _LOOP
