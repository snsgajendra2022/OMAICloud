"""Optional voice-clone adapter (disabled unless configured)."""
from __future__ import annotations

import os
from typing import Any


class VoiceCloneAdapter:
    def status(self) -> dict[str, Any]:
        enabled = (os.getenv("OM_VOICE_CLONE_ENABLED") or "0").strip() in {"1", "true", "yes"}
        profile = (os.getenv("OM_VOICE_CLONE_PROFILE") or "").strip()
        return {"enabled": enabled, "profile": profile or None, "ready": False}
