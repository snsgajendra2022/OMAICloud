"""Neural voice model handler — optional paid TTS (ElevenLabs / OpenAI)."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from .voice_profiles import jarvis_butler_profile

logger = logging.getLogger(__name__)

_SLNC = re.compile(r"\[\[slnc\s+\d+\]\]", re.I)
_BREAK_XML = re.compile(r"<break\s+\d+ms\s*/>", re.I)
_PLACEHOLDER_KEYS = {
    "",
    "your_key_here",
    "changeme",
    "xxx",
    "TODO",
    "replace_me",
}


def _ensure_env() -> None:
    try:
        from om_ai.env import load_dotenv

        load_dotenv()
    except Exception:
        pass


def _clean_for_neural(text: str) -> str:
    t = _SLNC.sub(" ", text or "")
    t = _BREAK_XML.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:2500]


def _neural_key() -> str:
    _ensure_env()
    key = (
        os.getenv("OM_NEURAL_TTS_API_KEY")
        or os.getenv("ELEVENLABS_API_KEY")
        or ""
    ).strip()
    if key.lower() in {k.lower() for k in _PLACEHOLDER_KEYS}:
        return ""
    return key


def _neural_provider() -> str:
    _ensure_env()
    return (os.getenv("OM_NEURAL_TTS_PROVIDER") or "").strip().lower()


class VoiceModel:
    """Handles optional neural TTS models. Free path does not use this."""

    def __init__(self) -> None:
        _ensure_env()
        self.profile = jarvis_butler_profile()

    def available(self) -> dict[str, Any]:
        st = self.status()
        return {"ok": bool(st.get("configured")), **st}

    def status(self) -> dict[str, Any]:
        provider = _neural_provider()
        key = _neural_key()
        return {
            "configured": bool(provider) and bool(key) and provider not in {"none", "off", "macos", "system"},
            "provider": provider or "none",
            "free": False,
            "streaming": provider in {"elevenlabs", "openai", "fish"},
            "voice_id": (
                os.getenv("OM_NEURAL_TTS_VOICE_ID")
                or os.getenv("OM_JARVIS_VOICE_ID")
                or ""
            ).strip()
            or None,
            "model": (os.getenv("OM_NEURAL_TTS_MODEL") or "eleven_multilingual_v2").strip(),
            "profile": self.profile.to_dict(),
            "needs_api_key": not bool(key),
        }

    def synthesize(
        self,
        text: str,
        *,
        output_path: str | Path | None = None,
        emotion: str = "calm",
    ) -> dict[str, Any]:
        _ = emotion  # applied upstream by EmotionVoice / ProsodyEngine
        provider = _neural_provider()
        if not provider or provider in {"none", "off", "macos", "system"}:
            return {"ok": False, "reason": "neural_tts_not_configured"}
        key = _neural_key()
        if not key:
            return {
                "ok": False,
                "reason": "missing_api_key",
                "hint": "Set OM_NEURAL_TTS_API_KEY only if you opt into paid neural TTS",
            }

        clean = _clean_for_neural(text)
        if not clean:
            return {"ok": False, "reason": "empty_text"}

        out = Path(output_path) if output_path else Path("/tmp/om_neural.mp3")
        try:
            if provider == "elevenlabs":
                return self._elevenlabs(clean, out, key)
            if provider == "openai":
                return self._openai(clean, out, key)
            return {"ok": False, "reason": f"unsupported_provider_{provider}"}
        except Exception as exc:
            logger.warning("neural voice model failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    def _elevenlabs(self, text: str, out: Path, key: str) -> dict[str, Any]:
        import urllib.request

        voice = (
            os.getenv("OM_NEURAL_TTS_VOICE_ID")
            or os.getenv("OM_JARVIS_VOICE_ID")
            or "JBFqnCBsd6RMkjVDRZzb"
        ).strip()
        model = (os.getenv("OM_NEURAL_TTS_MODEL") or "eleven_multilingual_v2").strip()
        settings = self.profile.elevenlabs_settings()
        for env_k, set_k in (
            ("OM_NEURAL_TTS_STABILITY", "stability"),
            ("OM_NEURAL_TTS_SIMILARITY", "similarity_boost"),
            ("OM_NEURAL_TTS_STYLE", "style"),
        ):
            raw = (os.getenv(env_k) or "").strip()
            if raw:
                try:
                    settings[set_k] = float(raw)
                except ValueError:
                    pass

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        body = json.dumps(
            {
                "text": text,
                "model_id": model,
                "voice_settings": settings,
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "xi-api-key": key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        out = out.with_suffix(".mp3")
        out.write_bytes(data)
        return {
            "ok": out.is_file() and out.stat().st_size > 100,
            "path": str(out),
            "backend": "elevenlabs",
            "voice": voice,
            "format": "mp3",
            "profile": self.profile.name,
        }

    def _openai(self, text: str, out: Path, key: str) -> dict[str, Any]:
        import urllib.request

        voice = (os.getenv("OM_NEURAL_TTS_VOICE_ID") or "onyx").strip()
        body = json.dumps(
            {
                "model": os.getenv("OM_NEURAL_TTS_MODEL") or "gpt-4o-mini-tts",
                "input": text,
                "voice": voice,
                "speed": float(os.getenv("OM_NEURAL_TTS_SPEED") or self.profile.speed),
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/speech",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        out = out.with_suffix(".mp3")
        out.write_bytes(data)
        return {
            "ok": out.is_file() and out.stat().st_size > 100,
            "path": str(out),
            "backend": "openai",
            "voice": voice,
            "format": "mp3",
            "profile": self.profile.name,
        }


# Back-compat alias
NeuralTTS = VoiceModel
