"""Neural TTS adapter — ElevenLabs / OpenAI / Fish when configured."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class NeuralTTS:
    def status(self) -> dict[str, Any]:
        provider = (os.getenv("OM_NEURAL_TTS_PROVIDER") or "").strip().lower()
        has_key = bool(
            (os.getenv("OM_NEURAL_TTS_API_KEY") or os.getenv("ELEVENLABS_API_KEY") or "").strip()
        )
        return {
            "configured": bool(provider) and has_key,
            "provider": provider or "none",
            "streaming": provider in {"elevenlabs", "openai", "fish"},
            "voice_id": (os.getenv("OM_NEURAL_TTS_VOICE_ID") or "").strip() or None,
        }

    def synthesize(self, text: str, *, output_path: str | Path | None = None) -> dict[str, Any]:
        provider = (os.getenv("OM_NEURAL_TTS_PROVIDER") or "").strip().lower()
        if not provider:
            return {"ok": False, "reason": "neural_tts_not_configured"}
        key = (os.getenv("OM_NEURAL_TTS_API_KEY") or os.getenv("ELEVENLABS_API_KEY") or "").strip()
        if not key:
            return {"ok": False, "reason": "missing_api_key"}

        out = Path(output_path) if output_path else Path("/tmp/om_neural.mp3")
        try:
            if provider == "elevenlabs":
                return self._elevenlabs(text, out, key)
            if provider == "openai":
                return self._openai(text, out, key)
            return {"ok": False, "reason": f"unsupported_provider_{provider}"}
        except Exception as exc:
            logger.warning("neural tts failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    def _elevenlabs(self, text: str, out: Path, key: str) -> dict[str, Any]:
        import urllib.request

        voice = (os.getenv("OM_NEURAL_TTS_VOICE_ID") or "JBFqnCBsd6RMkjVDRZzb").strip()
        model = (os.getenv("OM_NEURAL_TTS_MODEL") or "eleven_multilingual_v2").strip()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        body = (
            '{"text":'
            + __import__("json").dumps(text[:2500])
            + ',"model_id":'
            + __import__("json").dumps(model)
            + ',"voice_settings":{"stability":0.45,"similarity_boost":0.8,"style":0.35,"use_speaker_boost":true}}'
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
        }

    def _openai(self, text: str, out: Path, key: str) -> dict[str, Any]:
        import urllib.request
        import json

        voice = (os.getenv("OM_NEURAL_TTS_VOICE_ID") or "onyx").strip()
        body = json.dumps(
            {
                "model": os.getenv("OM_NEURAL_TTS_MODEL") or "gpt-4o-mini-tts",
                "input": text[:2500],
                "voice": voice,
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
        }
