"""Voice Intelligence façade → voice_intelligence + audio_intelligence."""
from __future__ import annotations

__all__ = ["VoiceRuntime", "get_voice_runtime"]


def get_voice_runtime():
    try:
        from om_ai.core.voice_intelligence.voice_runtime import VoiceRuntime

        return VoiceRuntime()
    except Exception:
        return None


class VoiceRuntime:
    """Thin proxy; prefer om_ai.core.voice_intelligence.voice_runtime."""

    def __init__(self) -> None:
        self._inner = None
        try:
            from om_ai.core.voice_intelligence.voice_runtime import VoiceRuntime as VR

            self._inner = VR()
        except Exception:
            self._inner = None

    def __getattr__(self, name: str):
        if self._inner is not None:
            return getattr(self._inner, name)
        raise AttributeError(name)
