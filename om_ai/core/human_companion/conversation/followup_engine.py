"""Follow-up engine — natural continuity without canned questions."""
from __future__ import annotations

import re
from typing import Any


class FollowupEngine:
    """Resolve references and decide whether a soft continuity hint is needed."""

    _REF = re.compile(
        r"\b(continue|continue that|keep going|us[ei]|that|this|it|same|"
        r"pehle wala|wahi|usko|uska|us pe|uspar)\b",
        re.I,
    )

    def analyze(
        self,
        text: str,
        *,
        state: dict[str, Any] | None = None,
        topic: str = "general",
        last_assistant: str = "",
        last_user: str = "",
    ) -> dict[str, Any]:
        low = (text or "").strip().lower()
        is_ref = bool(self._REF.search(low)) or len(low.split()) <= 4 and any(
            w in low for w in ("ha", "haan", "yes", "ok", "okay", "theek", "continue")
        )
        resolved = ""
        if is_ref:
            resolved = (last_user or last_assistant or topic or "").strip()
            if topic and topic != "general":
                resolved = f"{topic.replace('_', ' ')}: {resolved}"[:240]
        return {
            "is_followup": is_ref or bool(state and state.get("turn_count", 0) > 0 and len(low.split()) < 6),
            "is_reference": is_ref,
            "resolved_reference": resolved,
            "continuity_hint": (
                f"User is continuing the prior thread about {topic.replace('_', ' ')}."
                if is_ref and topic != "general"
                else ("User is continuing the prior conversation." if is_ref else "")
            ),
            # Never force a canned spoken follow-up question
            "append_spoken_followup": False,
        }
