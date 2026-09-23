"""Lip sync adapter."""
from __future__ import annotations

from typing import Any


class LipSync:
    def for_speech(self, text: str) -> dict[str, Any]:
        try:
            from om_ai.core.human_companion.avatar.lip_sync import LipSync as LS

            return LS().for_speech(text) if hasattr(LS(), "for_speech") else {"active": bool(text)}
        except Exception:
            return {"active": bool(text), "chars": len(text or "")}
