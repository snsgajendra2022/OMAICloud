"""Topic tracker — what the user is working on across turns."""
from __future__ import annotations

import re
from typing import Any


_TOPICS: dict[str, tuple[str, ...]] = {
    "voice_engine": ("voice", "tts", "stt", "speech", "microphone", "aman", "wake"),
    "avatar": ("avatar", "3d", "lip", "face", "presence", "animation"),
    "memory": ("memory", "remember", "preference", "yaad"),
    "actions": ("open", "youtube", "volume", "file", "app", "browser"),
    "coding": ("code", "bug", "error", "python", "function", "debug"),
    "project_om": ("om", "companion", "jarvis", "operating brain"),
    "weather": ("weather", "mausam", "temperature"),
}


class TopicTracker:
    def __init__(self) -> None:
        self._topic = "general"
        self._history: list[str] = []

    @property
    def current(self) -> str:
        return self._topic

    def update(self, text: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        low = (text or "").lower()
        hit = "general"
        best = 0
        for name, keys in _TOPICS.items():
            score = sum(1 for k in keys if k in low)
            if score > best:
                best = score
                hit = name
        # Continuity: short/reference utterances keep prior topic
        if best == 0 and self._is_reference(low) and self._topic != "general":
            hit = self._topic
        elif best == 0 and history:
            prior = " ".join(str(h.get("content") or "") for h in history[-4:]).lower()
            for name, keys in _TOPICS.items():
                if any(k in prior for k in keys):
                    hit = name
                    break
        if hit != "general":
            self._topic = hit
            self._history.append(hit)
            self._history = self._history[-12:]
        return {"topic": self._topic, "changed": best > 0, "history": list(self._history)[-5:]}

    def _is_reference(self, low: str) -> bool:
        return bool(
            re.search(
                r"\b(continue|us[ei]|that|this|it|same|pehle|wahi|usko|uska|continue that|keep going)\b",
                low,
            )
        )
