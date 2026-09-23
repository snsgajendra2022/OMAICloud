"""Speaking style — reshape answers for human companion voice."""
from __future__ import annotations

import re
from typing import Any

from om_ai.core.companion_personality.voice_presence import (
    is_garbage_spoken,
    rescue_spoken,
    shape_for_speech,
    strip_internal_chrome,
)


_BANNED_RE = re.compile(
    r"(?i)("
    r"how can i help you|how may i assist you|what can i (?:do|help) for you|"
    r"is there anything else(?: i can help you with)?|as an ai(?: language model)?|"
    r"i can help with that\.?|"
    r"got it(?:\s*[—\-–]\s*thinking)?\.?|"
    r"searching\.|"
    r"understanding request|"
    r"companion ready|"
    r"share one more detail(?:\s*\([^)]*\))?|"
    r"goal,\s*error,\s*or constraint|"
    r"share a bit more detail|"
    r"and i will give a concrete answer\.?"
    r")"
)


class SpeakingStyle:
    def reshape(self, answer: str, *, user_message: str = "", pack: dict[str, Any] | None = None) -> str:
        text = strip_internal_chrome(answer or "")
        text = _BANNED_RE.sub("", text).strip()
        text = re.sub(r"^[\s?.,!;:]+$", "", text).strip()
        text = re.sub(r"\s{2,}", " ", text)
        if not text or text.lower() in {"ok", "okay", "sure", "?", "!"} or is_garbage_spoken(text):
            text = rescue_spoken(user_message) if user_message else (
                "Bhai, samajh gaya — main check karta hun."
            )
        pack_out = shape_for_speech(text, user_message=user_message)
        spoken = str(pack_out.get("spoken") or text).strip()
        if is_garbage_spoken(spoken):
            spoken = rescue_spoken(user_message) if user_message else spoken
        return spoken
