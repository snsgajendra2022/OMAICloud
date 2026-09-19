"""Speaking style — reshape answers for human companion voice."""
from __future__ import annotations

import re
from typing import Any

from om_ai.core.companion_personality.voice_presence import shape_for_speech, strip_internal_chrome


_BANNED_RE = re.compile(
    r"(?i)\b("
    r"how can i help you|how may i assist you|what can i (?:do|help) for you|"
    r"is there anything else(?: i can help you with)?|as an ai(?: language model)?"
    r")\b[.!]?"
)


class SpeakingStyle:
    def reshape(self, answer: str, *, user_message: str = "", pack: dict[str, Any] | None = None) -> str:
        text = strip_internal_chrome(answer or "")
        text = _BANNED_RE.sub("", text).strip()
        text = re.sub(r"^[\s?.,!;:]+$", "", text).strip()
        text = re.sub(r"\s{2,}", " ", text)
        # Replace empty / generic with companion line
        if not text or text.lower() in {"ok", "okay", "sure", "?", "!"}:
            text = "Sir, I understand. Let me check this with you."
        pack_out = shape_for_speech(text, user_message=user_message)
        spoken = str(pack_out.get("spoken") or text).strip()
        # Soft Sir prefix when relationship asks and missing
        addr = str((pack or {}).get("relationship", {}).get("address") or "")
        if addr and not re.search(rf"(?i)\b{re.escape(addr)}\b", spoken[:40]):
            if not re.match(r"(?i)^(ji|theek|haan|yes|okay|ok)\b", spoken):
                # Don't force every line — only when reply is cold/generic
                if re.match(r"(?i)^(i (?:can|will|have)|let me|here)\b", spoken):
                    spoken = f"{addr}, {spoken[0].lower() + spoken[1:]}" if len(spoken) > 1 else spoken
        return spoken
