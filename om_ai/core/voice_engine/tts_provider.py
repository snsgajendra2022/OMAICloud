"""TTS provider — single entry for companion voice (free macOS default)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterator

from .emotion_voice import EmotionVoice
from .human_delivery import delivery_plan
from .lip_sync import LipSyncEngine
from .prosody_engine import ProsodyEngine
from .realtime_tts import RealtimeTTS
from .streaming_voice import StreamingVoice
from .voice_cloner import VoiceCloner
from .voice_model import VoiceModel
from .voice_profiles import VoiceProfiles

_ENGINE = None
_PLACEHOLDER = {"your_key_here", "changeme", "xxx", "todo", "replace_me", ""}


def _ensure_env() -> None:
    try:
        from om_ai.env import load_dotenv

        load_dotenv()
    except Exception:
        pass


def _api_key() -> str:
    _ensure_env()
    key = (
        os.getenv("OM_NEURAL_TTS_API_KEY")
        or os.getenv("ELEVENLABS_API_KEY")
        or os.getenv("AZURE_SPEECH_KEY")
        or ""
    ).strip()
    if key.lower() in _PLACEHOLDER:
        return ""
    return key


def active_provider() -> str:
    """Default free macos. Paid only with explicit provider + real key."""
    _ensure_env()
    companion = (os.getenv("OM_COMPANION_TTS_PROVIDER") or "macos").strip().lower()
    if companion in {"macos", "system", "say", "free", "off", ""}:
        return "macos"
    if companion not in {"neural", "elevenlabs", "openai", "azure"}:
        return "macos"
    if not _api_key():
        return "macos"
    neural = (os.getenv("OM_NEURAL_TTS_PROVIDER") or companion).strip().lower()
    if neural in {"none", "off", "macos", "system"}:
        return "macos"
    if companion == "neural":
        return neural if neural in {"elevenlabs", "openai", "azure"} else "elevenlabs"
    return companion


def _prefer_neural() -> bool:
    return active_provider() not in {"macos", "system"}


class TTSProvider:
    """One facade: plan → synthesize → optional realtime stream."""

    def __init__(self) -> None:
        _ensure_env()
        self.profiles = VoiceProfiles()
        self.prosody = ProsodyEngine()
        self.emotion = EmotionVoice()
        self.model = VoiceModel()
        self.stream = StreamingVoice()
        self.realtime = RealtimeTTS()
        self.lips = LipSyncEngine()
        self.clone = VoiceCloner()
        self._fallback = None

    def _synth(self):
        if self._fallback is None:
            from om_ai.core.voice_intelligence.speech_synthesizer import SpeechSynthesizer

            self._fallback = SpeechSynthesizer()
        return self._fallback

    def status(self) -> dict[str, Any]:
        s = self._synth().status()
        provider = active_provider()
        return {
            "ready": True,
            "name": "OM Voice Engine",
            "provider": provider,
            "default": "macos",
            "free": provider == "macos",
            "backend": s.get("backend") if provider == "macos" else provider,
            "voice": s.get("voice"),
            "rate": s.get("rate"),
            "profile": self.profiles.get(),
            "neural": self.model.status(),
            "realtime": self.realtime.status(),
            "clone": self.clone.status(),
            "human_ceiling": "system_tts" if provider == "macos" else "neural_tts",
            "steps": {
                "tts_provider": True,
                "realtime": bool((self.realtime.status() or {}).get("ready")),
                "emotion_streaming": True,
                "lip_sync": True,
                "human_delivery": True,
            },
        }

    def speak_plan(
        self,
        text: str,
        *,
        emotion: str = "calm",
        presence: str = "speaking",
    ) -> dict[str, Any]:
        knobs = self.emotion.map(emotion)
        styled = self.emotion.apply(text, emotion=emotion)
        if not _prefer_neural():
            human = delivery_plan(styled, emotion=emotion)
            paced = str(human.get("spoken_tts") or styled)
            clean = str(human.get("spoken_clean") or styled)
            rate = human.get("rate")
            # Audio already paced by macOS [[rate]] — never slow again in browser
            knobs = {**knobs, "rate": 1.0}
            human = {**human, "browser_rate": 1.0}
        else:
            clean = styled
            paced = self.prosody.apply(styled, presence=presence)
            rate = knobs.get("wpm") or knobs.get("rate")
            human = {
                "spoken_clean": clean,
                "rate": rate,
                "voice": "neural",
                "browser_rate": knobs.get("rate") or 1.0,
            }
        chunks = list(self.stream.chunks(clean))
        lips = self.lips.from_text(clean, emotion=emotion)
        return {
            "text": paced,
            "spoken_clean": clean,
            "emotion": emotion,
            "emotion_knobs": knobs,
            "presence": presence,
            "streamable": True,
            "chunks": chunks,
            "lips": lips,
            "rate": rate,
            "voice": human.get("voice") or self.profiles.get().get("voice_id") or "Aman",
            "browser_rate": human.get("browser_rate") or knobs.get("rate") or 1.0,
            "provider": active_provider(),
            "free": not _prefer_neural(),
        }

    def synthesize(
        self,
        text: str,
        *,
        output_path: str | Path | None = None,
        emotion: str = "calm",
        presence: str = "speaking",
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        plan = plan or self.speak_plan(text, emotion=emotion, presence=presence)
        spoken = str(plan.get("text") or text)
        provider = active_provider()
        if provider != "macos":
            neural = self.model.synthesize(
                plan.get("spoken_clean") or spoken,
                output_path=output_path,
                emotion=emotion,
            )
            if neural.get("ok"):
                return {
                    **neural,
                    "plan": plan,
                    "provider": provider,
                    "free": False,
                    "lips": plan.get("lips"),
                }
            plan = {**plan, "neural_error": neural}
        out = self._synth().synthesize(
            spoken,
            output_path=output_path,
            emotion=emotion,
            preplanned=True,
        )
        return {
            **out,
            "plan": plan,
            "provider": out.get("backend") or "macos",
            "free": True,
            "lips": plan.get("lips"),
        }

    def stream_audio(
        self,
        text: str,
        *,
        emotion: str = "calm",
        presence: str = "speaking",
    ) -> Iterator[bytes]:
        plan = self.speak_plan(text, emotion=emotion, presence=presence)
        provider = active_provider()
        if provider in {"elevenlabs", "azure", "openai"}:
            yield from self.realtime.stream(
                str(plan.get("spoken_clean") or plan.get("text") or text),
                provider=provider,
                emotion_knobs=plan.get("emotion_knobs") or {},
            )


VoiceProvider = TTSProvider


def get_voice_engine() -> TTSProvider:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = TTSProvider()
    return _ENGINE
