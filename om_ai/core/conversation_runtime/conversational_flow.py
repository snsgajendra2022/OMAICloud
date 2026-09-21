"""OM conversational flow — dynamic topic + continuity (no canned follow-ups)."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any


_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are", "was",
    "i", "you", "we", "me", "my", "it", "this", "that", "with", "from", "be", "do",
    "hai", "hain", "kya", "ki", "ka", "ke", "se", "mein", "main", "nahi", "nahin",
    "please", "just", "like", "can", "will", "would", "could", "should",
}


class ConversationalFlow:
    """Tracks live topic from tokens + history; never injects spoken canned Qs."""

    def __init__(self) -> None:
        self.topic_memory: dict[str, str] = {}
        self._token_memory: dict[str, Counter[str]] = {}
        self._seed_topics: dict[str, tuple[str, ...]] = {
            "model_pipeline": ("model", "llm", "training", "checkpoint", "weights", "dataset", "inference"),
            "voice_system": ("voice", "tts", "speech", "microphone", "audio", "listen", "aman"),
            "avatar_system": ("avatar", "3d", "animation", "face", "lip", "presence"),
            "memory_system": ("memory", "remember", "preference", "history", "context"),
            "om_project": ("om", "companion", "jarvis", "operating"),
            "debugging": ("bug", "error", "exception", "failed", "crash", "issue"),
            "planning": ("plan", "roadmap", "architecture", "design", "build"),
        }

    def _tokens(self, text: str) -> list[str]:
        raw = re.findall(r"[a-zA-Z\u0900-\u097F]{3,}", (text or "").lower())
        return [t for t in raw if t not in _STOP]

    def infer_topic(self, text: str, *, session_id: str = "") -> str:
        blob = (text or "").lower()
        scores: dict[str, float] = {}
        for topic, keywords in self._seed_topics.items():
            score = float(sum(1 for w in keywords if w in blob))
            if score:
                scores[topic] = score

        # Dynamic: boost session-frequent tokens as a soft topic label
        toks = self._tokens(text)
        if session_id and session_id in self._token_memory:
            prior = self._token_memory[session_id]
            for t in toks:
                if prior.get(t, 0) >= 2:
                    scores[t] = scores.get(t, 0) + 0.5 + prior[t] * 0.1

        if not scores:
            # Reference utterances keep prior topic
            if session_id and self.topic_memory.get(session_id) and re.search(
                r"\b(continue|that|this|it|wahi|usko|pehle)\b", blob
            ):
                return self.topic_memory[session_id]
            return "general"
        return max(scores, key=scores.get)

    def update_context(self, session_id: str, text: str) -> str:
        topic = self.infer_topic(text, session_id=session_id)
        if session_id:
            self.topic_memory[session_id] = topic
            bag = self._token_memory.setdefault(session_id, Counter())
            bag.update(self._tokens(text))
            # Cap bag size
            if len(bag) > 80:
                for k, _ in bag.most_common()[60:]:
                    del bag[k]
        return topic

    def current_topic(self, session_id: str) -> str:
        return self.topic_memory.get(session_id, "general")

    def continuity_hint(
        self,
        user_text: str,
        *,
        session_id: str = "",
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Metadata for the brain — not a spoken append."""
        topic = self.current_topic(session_id) if session_id else self.infer_topic(user_text)
        low = (user_text or "").lower()
        is_ref = bool(re.search(r"\b(continue|that|this|it|wahi|usko|pehle|keep going)\b", low))
        prior = ""
        if history:
            for h in reversed(history):
                if h.get("role") == "user" and str(h.get("content") or "").strip():
                    prior = str(h["content"]).strip()[:160]
                    break
        hint = ""
        if is_ref and (topic != "general" or prior):
            hint = f"Continuing prior thread ({topic}): {prior or topic}"
        return {
            "topic": topic,
            "is_reference": is_ref,
            "prior_user": prior,
            "hint": hint,
        }

    def should_follow_up(
        self,
        answer: str,
        user_text: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Never auto-append spoken follow-ups."""
        del answer, user_text, context
        return False

    def follow_up(
        self,
        user_text: str,
        answer: str,
        *,
        topic: str = "",
        session_id: str = "",
    ) -> str | None:
        del user_text, answer, topic, session_id
        return None

    def merge_follow_up(self, answer: str, follow: str | None) -> str:
        del follow
        return (answer or "").strip()

    def already_asks(self, answer: str) -> bool:
        text = (answer or "").strip()
        if not text:
            return False
        if "?" in text or "؟" in text:
            return True
        return bool(re.search(r"(kya|kia|batao|boliye)\b", text.lower()))
