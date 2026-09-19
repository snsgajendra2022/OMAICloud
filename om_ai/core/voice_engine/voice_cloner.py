"""Custom authorized voice training adapter — opt-in only, never default."""
from __future__ import annotations

import os
from typing import Any


class VoiceCloner:
    """
    Placeholder for authorized custom voice clone workflows.

    Disabled unless OM_VOICE_CLONE_ENABLED=1 and a lawful profile is set.
    Does not clone copyrighted film/celebrity voices.
    """

    def status(self) -> dict[str, Any]:
        enabled = (os.getenv("OM_VOICE_CLONE_ENABLED") or "0").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        profile = (os.getenv("OM_VOICE_CLONE_PROFILE") or "").strip()
        return {
            "enabled": enabled,
            "profile": profile or None,
            "ready": False,
            "authorized_only": True,
            "note": "Requires explicit consent + your own voice samples. Off by default.",
        }

    def train(self, *, samples_dir: str | None = None, name: str = "custom") -> dict[str, Any]:
        st = self.status()
        if not st["enabled"]:
            return {"ok": False, "reason": "voice_clone_disabled"}
        if not samples_dir:
            return {"ok": False, "reason": "samples_dir_required"}
        return {
            "ok": False,
            "reason": "not_implemented",
            "name": name,
            "samples_dir": samples_dir,
            "hint": "Wire your authorized clone provider when you opt in.",
        }


# Back-compat alias
VoiceCloneAdapter = VoiceCloner
