"""STEP 71.1 — Human Presence Engine (complete turn gate).

Flow:
  Voice/Text
    → Human Meaning Analyzer (emotion + intent + context)
    → Personality Brain (care / humor / empathy / relationship)
    → Intelligence Router decision (listen | answer | search | action)
    → Permission Controller (if action)
    → Response plan for Voice + Expression
"""
from __future__ import annotations

import re
from typing import Any

_ENGINE: "HumanPresenceEngine | None" = None


class HumanPresenceEngine:
    """Gate that stops robotic solve/search-box behavior."""

    STEP = 71
    PRINCIPLES = (
        "Understand before answering.",
        "Do not answer only keywords.",
        "Detect user's emotional state.",
        "If user is sharing feelings, listen first.",
        "Ask natural follow-up questions.",
        "Do not over-explain simple things.",
        "Do not interrupt incomplete speech.",
        "Remember conversation history.",
        "Be warm but honest.",
        "Never pretend to be human.",
    )

    def __init__(self) -> None:
        from om_ai.core.human_intelligence.human_meaning_engine import HumanMeaningEngine
        from om_ai.core.human_intelligence.human_intent_engine import HumanIntentEngine
        from om_ai.core.human_intelligence.conversation_feeling import ConversationFeeling
        from om_ai.core.human_intelligence.user_state import UserState
        from om_ai.core.human_intelligence.response_behavior import ResponseBehavior
        from om_ai.core.emotion_intelligence.emotion_state import EmotionState
        from om_ai.core.emotion_intelligence.emotion_detector import EmotionDetector
        from om_ai.core.emotion_intelligence.empathy_engine import EmpathyEngine
        from om_ai.core.emotion_intelligence.tone_controller import ToneController
        from om_ai.core.action_control.action_policy import ActionPolicy
        from om_ai.core.action_control.execution_guard import ExecutionGuard
        from om_ai.core.personality.conversation_principles import ConversationPrinciples

        self.meaning = HumanMeaningEngine()
        self.intent = HumanIntentEngine()
        self.feeling = ConversationFeeling()
        self.user_state = UserState()
        self.behavior = ResponseBehavior()
        self.emotion_state = EmotionState()
        self.emotion_detector = EmotionDetector()
        self.empathy = EmpathyEngine()
        self.tone = ToneController()
        self.action_policy = ActionPolicy()
        self.execution_guard = ExecutionGuard()
        self.principles = ConversationPrinciples()

    def analyze(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        profile: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> dict[str, Any]:
        text = (message or "").strip()
        hist = history or []
        profile = profile or {}

        # —— Emotion (honest detection, not fake feelings) ——
        det = self.emotion_detector.detect(text, history=hist)
        emo_label = str(det.get("emotion") or "neutral")
        emo_state = self.emotion_state.update(emo_label, confidence=float(det.get("confidence") or 0.55))
        empathy = self.empathy.guide(emo_label, need="")
        tone = self.tone.for_emotion(emo_label) if hasattr(self.tone, "for_emotion") else (
            self.tone.apply(emo_label) if hasattr(self.tone, "apply") else {"tone": "warm"}
        )

        # —— Meaning: why they said it ——
        meaning = self.meaning.understand(
            text,
            history=hist,
            emotion={"label": emo_label, "emotion": emo_label, **det},
        )
        intent = self.intent.infer(text, history=hist, meaning=meaning)
        feeling = self.feeling.read(
            emotion={"emotion": emo_label, "label": emo_label, **det},
            human=meaning.get("pack") or {},
        )

        # —— User state ——
        state = self.user_state.update(
            emotion=emo_label,
            topic=str((meaning.get("pack") or {}).get("topic") or "general"),
            intent=str(intent.get("intent") or "conversation"),
            name=str(profile.get("name") or ""),
        )

        # —— Route: listen | answer | search | action | joke | think ——
        route = self._route(text, meaning=meaning, intent=intent, emotion=emo_label, feeling=feeling)

        # —— Action policy: search ≠ open ——
        policy = self.action_policy.classify(text)
        guard = self.execution_guard.check(policy)

        # —— Response behavior (what OM should do next) ——
        behavior = self.behavior.decide(
            meaning=meaning,
            intent=intent,
            feeling=feeling,
            emotion=emo_label,
            route=route,
            locale=locale,
        )

        # Seed natural reply when listen-first / sharing
        seed = str(behavior.get("seed_reply") or "").strip()
        if not seed and route.get("mode") == "listen" and meaning.get("natural_ask"):
            seed = str(meaning["natural_ask"])
        if not seed and empathy.get("ack_line") and route.get("mode") == "listen":
            ask = meaning.get("natural_ask") or behavior.get("followup") or ""
            seed = f"{empathy['ack_line']} {ask}".strip()

        system_hint = self._compose_hint(
            meaning=meaning,
            intent=intent,
            feeling=feeling,
            empathy=empathy,
            route=route,
            policy=policy,
            guard=guard,
            behavior=behavior,
            locale=locale,
        )

        return {
            "step": self.STEP,
            "text": text,
            "meaning": meaning,
            "intent": intent,
            "feeling": feeling,
            "emotion": {
                **det,
                "state": emo_state,
                "empathy": empathy,
                "tone": tone,
                # Honest: OM understands affect — does not claim to *feel* it
                "om_has_feelings": False,
                "om_shows_empathy": True,
            },
            "user_state": state,
            "route": route,
            "action_policy": policy,
            "execution_guard": guard,
            "behavior": behavior,
            "seed_reply": seed,
            "listen_first": bool(route.get("mode") == "listen" or meaning.get("needs_listening")),
            "block_solution_engine": bool(
                route.get("mode") in {"listen", "share", "joke"}
                or meaning.get("needs_listening")
            ),
            "allow_search": bool(policy.get("kind") == "search" and guard.get("allowed")),
            "allow_open": bool(policy.get("kind") == "open" and guard.get("allowed")),
            "requires_permission": bool(guard.get("requires_permission")),
            "permission_prompt": guard.get("prompt") or "",
            "system_hint": system_hint,
            "principles": list(self.PRINCIPLES),
            "avatar_state": (
                "listening" if route.get("mode") == "listen" else (
                    "thinking" if route.get("mode") in {"think", "search", "reason"} else "speaking"
                )
            ),
        }

    def _route(
        self,
        text: str,
        *,
        meaning: dict[str, Any],
        intent: dict[str, Any],
        emotion: str,
        feeling: dict[str, Any],
    ) -> dict[str, Any]:
        low = (text or "").lower()
        if meaning.get("needs_listening") or feeling.get("need") == "conversation":
            return {"mode": "listen", "reason": "user_sharing_feelings"}
        if intent.get("intent") == "joke" or re.search(r"(?i)\b(joke|majaak|lol|haha)\b", low):
            return {"mode": "joke", "reason": "playful"}
        if intent.get("intent") == "research" or re.search(
            r"(?i)\b(search|google|khoj|research|look up|find)\b", low
        ):
            return {"mode": "search", "reason": "information_request"}
        if intent.get("intent") == "action" or re.search(
            r"(?i)\b(open|kholo|launch|delete|send|run)\b", low
        ):
            return {"mode": "action", "reason": "action_request"}
        if intent.get("intent") in {"question", "problem"} or "?" in text:
            return {"mode": "answer", "reason": "question"}
        if emotion in {"confused"} or re.search(r"(?i)\b(thinking|soch|hmm+)\b", low):
            return {"mode": "think", "reason": "reflective"}
        if emotion in {"happy", "excited"}:
            return {"mode": "share", "reason": "positive_affect"}
        return {"mode": "answer", "reason": "default_assist"}

    def _compose_hint(self, **packs: Any) -> str:
        meaning = packs.get("meaning") or {}
        intent = packs.get("intent") or {}
        feeling = packs.get("feeling") or {}
        empathy = packs.get("empathy") or {}
        route = packs.get("route") or {}
        policy = packs.get("policy") or {}
        guard = packs.get("guard") or {}
        behavior = packs.get("behavior") or {}
        locale = packs.get("locale") or "en"

        lines = [
            "STEP 71 Human Presence: understand WHY before answering.",
            "You are OM — a companion. Warm, honest. Never pretend to be human.",
            "Never say: How can I help you / As an AI / Explain your problem.",
            f"Route: {route.get('mode')} ({route.get('reason')}).",
            f"Intent: {intent.get('intent')} — need: {feeling.get('need')}.",
            f"Response style: {behavior.get('style') or feeling.get('response') or 'balanced'}.",
        ]
        if meaning.get("needs_listening"):
            lines.append("LISTEN FIRST. Acknowledge feeling. One gentle question. Do not solve yet.")
        if empathy.get("ack_line"):
            lines.append(f"Empathy cue: {empathy['ack_line']}")
        if policy.get("kind") == "search":
            lines.append("SEARCH ONLY — report findings. Do NOT open/redirect browser unless user says go/open/kholo.")
        if guard.get("requires_permission"):
            lines.append(f"PERMISSION REQUIRED before action: {guard.get('prompt')}")
        if locale == "hi":
            lines.append("Mirror warm Hinglish / bhai tone when natural.")
        lines.append("Principles: " + " | ".join(self.PRINCIPLES[:5]))
        return "\n".join(lines)


def get_human_presence() -> HumanPresenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = HumanPresenceEngine()
    return _ENGINE


def run_human_presence(
    message: str,
    *,
    history: list[dict[str, Any]] | None = None,
    profile: dict[str, Any] | None = None,
    locale: str = "en",
) -> dict[str, Any]:
    return get_human_presence().analyze(
        message, history=history, profile=profile, locale=locale
    )
