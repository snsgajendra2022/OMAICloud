"""Context engine — builds rich turn context for the brain."""
from __future__ import annotations

from typing import Any


class ContextEngine:
    def build(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        topic: str = "general",
        memory_blob: str = "",
        emotion: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        followup: dict[str, Any] | None = None,
        task: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hist = history or []
        parts: list[str] = []
        name = str((profile or {}).get("name") or "").strip()
        if name:
            parts.append(f"User name: {name}. Address naturally (Sir/Ji when fitting).")
        if topic and topic != "general":
            parts.append(f"Active topic: {topic.replace('_', ' ')}.")
        if followup and followup.get("continuity_hint"):
            parts.append(str(followup["continuity_hint"]))
        if followup and followup.get("resolved_reference"):
            parts.append(f"Resolved reference: {followup['resolved_reference'][:200]}")
        if emotion:
            label = emotion.get("label") or emotion.get("emotion") or "neutral"
            if label and label != "neutral":
                parts.append(f"User emotion: {label}. Match tone with care.")
        if memory_blob:
            parts.append(f"Memory:\n{memory_blob[:1400]}")
        if task and task.get("summary"):
            parts.append(f"Task context: {task['summary'][:200]}")
        # Recent dialogue
        if hist:
            lines = []
            for h in hist[-6:]:
                role = str(h.get("role") or "?")
                content = str(h.get("content") or "").strip()[:180]
                if content:
                    lines.append(f"{role}: {content}")
            if lines:
                parts.append("Recent turns:\n" + "\n".join(lines))
        blob = "\n".join(parts).strip()
        return {
            "context_blob": blob[:3200],
            "topic": topic,
            "followup": followup or {},
            "emotion": emotion or {},
            "profile": profile or {},
            "message": message,
        }
