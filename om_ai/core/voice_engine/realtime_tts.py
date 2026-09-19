"""STEP 2 — ElevenLabs / Azure realtime TTS streaming (optional / paid)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Iterator

logger = logging.getLogger(__name__)

_PLACEHOLDER = {"your_key_here", "changeme", "xxx", "todo", "replace_me", ""}


def _ensure_env() -> None:
    try:
        from om_ai.env import load_dotenv

        load_dotenv()
    except Exception:
        pass


def _key(*names: str) -> str:
    _ensure_env()
    for n in names:
        v = (os.getenv(n) or "").strip()
        if v and v.lower() not in _PLACEHOLDER:
            return v
    return ""


class RealtimeTTS:
    """Streams audio bytes from cloud TTS. Disabled unless keys + provider set."""

    def status(self) -> dict[str, Any]:
        el = bool(_key("OM_NEURAL_TTS_API_KEY", "ELEVENLABS_API_KEY"))
        az = bool(_key("AZURE_SPEECH_KEY")) and bool(
            (os.getenv("AZURE_SPEECH_REGION") or "").strip()
        )
        provider = (os.getenv("OM_NEURAL_TTS_PROVIDER") or "").strip().lower()
        ready = (provider == "elevenlabs" and el) or (provider == "azure" and az)
        return {
            "ready": ready,
            "elevenlabs": el,
            "azure": az,
            "provider": provider or None,
            "mode": "stream" if ready else "off",
            "free": False,
            "note": "Realtime cloud TTS is optional. Default companion voice is free macOS.",
        }

    def stream(
        self,
        text: str,
        *,
        provider: str = "elevenlabs",
        emotion_knobs: dict[str, Any] | None = None,
    ) -> Iterator[bytes]:
        clean = (text or "").strip()
        if not clean:
            return
        p = (provider or "").strip().lower()
        try:
            if p == "elevenlabs":
                yield from self._elevenlabs_stream(clean, emotion_knobs or {})
            elif p == "azure":
                yield from self._azure_stream(clean, emotion_knobs or {})
            elif p == "openai":
                yield from self._openai_once(clean)
            else:
                return
        except Exception as exc:
            logger.warning("realtime tts stream failed: %s", exc)
            return

    def _elevenlabs_stream(
        self, text: str, knobs: dict[str, Any]
    ) -> Iterator[bytes]:
        import urllib.request

        key = _key("OM_NEURAL_TTS_API_KEY", "ELEVENLABS_API_KEY")
        if not key:
            return
        voice = (
            os.getenv("OM_NEURAL_TTS_VOICE_ID")
            or os.getenv("OM_JARVIS_VOICE_ID")
            or "JBFqnCBsd6RMkjVDRZzb"
        ).strip()
        model = (os.getenv("OM_NEURAL_TTS_MODEL") or "eleven_multilingual_v2").strip()
        settings = {
            "stability": float(knobs.get("stability", 0.55)),
            "similarity_boost": float(knobs.get("similarity", 0.75)),
            "style": float(knobs.get("style", 0.35)),
            "use_speaker_boost": True,
        }
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream"
            f"?optimize_streaming_latency=3&output_format=mp3_44100_128"
        )
        body = json.dumps(
            {"text": text[:2500], "model_id": model, "voice_settings": settings}
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                yield chunk

    def _azure_stream(
        self, text: str, knobs: dict[str, Any]
    ) -> Iterator[bytes]:
        import urllib.request

        key = _key("AZURE_SPEECH_KEY")
        region = (os.getenv("AZURE_SPEECH_REGION") or "").strip()
        if not key or not region:
            return
        voice = (
            os.getenv("AZURE_SPEECH_VOICE")
            or "en-GB-RyanNeural"
        ).strip()
        rate = float(knobs.get("rate", 0.92))
        pct = int((rate - 1.0) * 100)
        ssml = (
            f"<speak version='1.0' xml:lang='en-GB'>"
            f"<voice name='{voice}'>"
            f"<prosody rate='{pct}%'>{_xml_escape(text[:2500])}</prosody>"
            f"</voice></speak>"
        )
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        req = urllib.request.Request(
            url,
            data=ssml.encode("utf-8"),
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
                "User-Agent": "om-ai-companion",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                yield chunk

    def _openai_once(self, text: str) -> Iterator[bytes]:
        import urllib.request

        key = _key("OM_NEURAL_TTS_API_KEY", "OPENAI_API_KEY")
        if not key:
            return
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                yield chunk


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
