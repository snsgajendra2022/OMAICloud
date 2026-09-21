"""Dynamic response strategy from meaning, emotion, policy, and friend stance."""
from __future__ import annotations

from typing import Any


class ResponseStrategy:
    def select(
        self,
        semantic: dict[str, Any],
        policy: dict[str, Any],
        *,
        emotion: dict[str, Any] | None = None,
        friend: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        mode = str(semantic.get("conversation_mode") or "assist")
        intent = str(semantic.get("intent") or "chat")
        emo = str((emotion or {}).get("label") or (emotion or {}).get("emotion") or "neutral")
        friend_move = str((friend or {}).get("friend_move") or "")
        pol = str((policy or {}).get("policy") or "balanced_assist")

        style = "balanced"
        max_sentences = int((policy or {}).get("max_sentences") or 3)
        tone = str((policy or {}).get("tone") or "calm")

        if semantic.get("requires_action") or mode == "task":
            style = "action_confirm"
            max_sentences = 2
            tone = "focused"
        elif friend_move == "be_more_human" or emo in {"frustration", "stress"}:
            style = "empathic_companion"
            max_sentences = 2
            tone = "soft"
        elif friend_move == "pick_up_thread" or mode == "continue" or intent == "followup":
            style = "thread_continuity"
            max_sentences = 3
            tone = "calm"
        elif mode == "social" or intent in {"greeting", "thanks", "goodbye"}:
            style = "social_brief"
            max_sentences = 2
            tone = "warm"
        elif mode == "clarify" or friend_move == "one_gentle_question":
            style = "one_question"
            max_sentences = 2
            tone = "warm"
        elif semantic.get("requires_model") or mode in {"assist", "listen"}:
            style = "explainer" if mode != "social" else "conversational"
            max_sentences = 3

        return {
            "engine": "chatgpt_runtime",
            "style": style,
            "use_model": True,
            "max_sentences": max_sentences,
            "tone": tone,
            "policy": pol,
            "friend_move": friend_move,
            "skip_canned": True,
            "instruction": (
                f"Style={style}. Tone={tone}. At most {max_sentences} short spoken sentences. "
                "Speak like a loyal friend/companion. No chatbot openers."
            ),
        }
