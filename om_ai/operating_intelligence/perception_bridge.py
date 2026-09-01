"""Perception bridge — voice / vision / multimodal (null-safe)."""
from __future__ import annotations

from typing import Any


def status() -> dict[str, Any]:
    voice = "stub"
    vision = "stub"
    try:
        from om_ai.voice import NullSpeechBackend  # noqa: F401

        voice = "null_backend_ready"
    except Exception:
        pass
    try:
        from om_ai.vision import NullVisionBackend  # noqa: F401

        vision = "null_backend_ready"
    except Exception:
        pass
    return {
        "voice": voice,
        "vision": vision,
        "note": "Connect Whisper/VITS or cloud STT-TTS and a vision encoder for production.",
    }


def describe_image(_path: str = "") -> dict[str, Any]:
    return {"ok": False, "status": "vision_backend_not_configured"}


def transcribe_audio(_path: str = "") -> dict[str, Any]:
    return {"ok": False, "status": "speech_backend_not_configured"}
