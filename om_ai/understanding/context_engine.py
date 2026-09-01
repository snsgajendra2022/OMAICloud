"""Context Intelligence — conversation, project, preferences, prior decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from om_ai.understanding.context_analyzer import ContextSnapshot, analyze_context


@dataclass
class ContextIntelligence:
    conversation: list[str] = field(default_factory=list)
    project_topic: str = ""
    preferences: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    resolved_followup: str = ""
    summary: str = ""
    snapshot: ContextSnapshot | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation": self.conversation,
            "project_topic": self.project_topic,
            "preferences": self.preferences,
            "decisions": self.decisions,
            "resolved_followup": self.resolved_followup,
            "summary": self.summary,
        }


def gather_context(
    messages: list[dict[str, Any]] | None,
    *,
    project_instructions: str = "",
    memory_snippets: list[str] | None = None,
    current_text: str = "",
    tenant_id: str = "default",
    user_id: str = "",
) -> ContextIntelligence:
    snap = analyze_context(
        messages,
        project_instructions=project_instructions,
        memory_snippets=memory_snippets,
        current_text=current_text,
    )
    prefs: list[str] = []
    decisions: list[str] = []
    if user_id:
        try:
            from om_ai.memory.layers import LayeredMemory

            mem = LayeredMemory(tenant_id=tenant_id, user_id=user_id)
            for layer, bucket in (("user", prefs), ("experience", decisions), ("project", decisions)):
                for h in mem.recall(current_text or snap.project_topic or "session", layer=layer, k=3) or []:
                    text = str(h.get("content") or h.get("text") or "").strip()
                    if text:
                        bucket.append(text[:200])
        except Exception:
            pass
    for mem in (memory_snippets or [])[:3]:
        if mem.strip() and mem.strip() not in prefs:
            prefs.append(mem.strip()[:160])
    bits = [snap.summary] if snap.summary else []
    if prefs:
        bits.append("Preferences: " + "; ".join(prefs[:2]))
    if decisions:
        bits.append("Prior decisions: " + "; ".join(decisions[:2]))
    return ContextIntelligence(
        conversation=list(snap.recent_user[-4:]),
        project_topic=snap.project_topic,
        preferences=prefs[:5],
        decisions=decisions[:5],
        resolved_followup=snap.resolved_followup,
        summary=" ".join(bits).strip(),
        snapshot=snap,
    )
