"""TTS provider abstraction with graceful fallbacks — natural Jarvis-like voice."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Prefer calm conversational voices; Rishi for Hindi/Hinglish when selected
_PREFERRED_VOICES = (
    "Daniel",
    "Rishi",
    "Moira",
    "Samantha",
    "Karen",
    "Alex",
)
_HINDI_VOICES = ("Rishi", "Veena", "Lekha", "Moira", "Samantha")


class SpeechSynthesizer:
    def __init__(self) -> None:
        self._backend = "none"
        self._error: str | None = None
        self._voice: str | None = None
        self._rate = int(os.getenv("OM_COMPANION_TTS_RATE") or "132")
        self._detect()

    def _detect(self) -> None:
        if shutil.which("say"):
            self._backend = "macos_say"
            self._voice = self._pick_macos_voice()
            return
        try:
            import pyttsx3  # noqa: F401

            self._backend = "pyttsx3"
            return
        except Exception as exc:
            self._error = str(exc)
        try:
            from om_ai.voice.text_to_speech import TextToSpeech  # noqa: F401

            self._backend = "om_voice_tts"
        except Exception as exc:
            self._error = f"{self._error}; {exc}"

    def _pick_macos_voice(self) -> str | None:
        forced = (os.getenv("OM_COMPANION_TTS_VOICE") or "").strip()
        if forced:
            return forced
        return self._pick_voice_from(_PREFERRED_VOICES) or "Daniel"

    def _pick_voice_from(self, names: tuple[str, ...]) -> str | None:
        try:
            out = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                check=False,
            )
            available = out.stdout or ""
            for name in names:
                if name in available:
                    return name
        except Exception as exc:
            logger.debug("voice probe failed: %s", exc)
        return None

    @property
    def ready(self) -> bool:
        return self._backend != "none"

    def status(self) -> dict[str, Any]:
        return {
            "backend": self._backend,
            "ready": self.ready,
            "error": self._error,
            "voice": self._voice,
            "rate": self._rate,
        }

    def synthesize(self, text: str, *, output_path: str | Path | None = None) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty"}
        out = Path(output_path) if output_path else Path(tempfile.mkstemp(suffix=".aiff")[1])
        try:
            if self._backend == "macos_say":
                voice = self._voice
                # Auto-pick Indian English voice for Hindi/Hinglish content
                try:
                    from om_ai.core.companion_personality.voice_presence import detect_speech_locale

                    if detect_speech_locale(text) == "hi":
                        voice = self._pick_voice_from(_HINDI_VOICES) or voice
                except Exception:
                    pass
                cmd = ["say", "-o", str(out), "-r", str(self._rate)]
                if voice:
                    cmd.extend(["-v", voice])
                if out.suffix.lower() == ".wav":
                    cmd.extend(["--data-format=LEI16@22050"])
                cmd.append(text)
                subprocess.run(cmd, check=False, capture_output=True)
                return {
                    "ok": out.exists() and out.stat().st_size > 44,
                    "path": str(out),
                    "backend": self._backend,
                    "voice": voice,
                    "text": text,
                }
            if self._backend == "pyttsx3":
                import pyttsx3

                eng = pyttsx3.init()
                eng.setProperty("rate", self._rate)
                eng.save_to_file(text, str(out.with_suffix(".wav")))
                eng.runAndWait()
                path = out.with_suffix(".wav")
                return {"ok": path.exists(), "path": str(path), "backend": self._backend, "text": text}
            if self._backend == "om_voice_tts":
                from om_ai.voice.text_to_speech import TextToSpeech

                result = TextToSpeech().generate(text)
                return {"ok": True, "path": None, "backend": self._backend, "result": result, "text": text}
            return {"ok": False, "reason": "tts_unavailable", "text": text, "backend": self._backend}
        except Exception as exc:
            logger.warning("TTS failed: %s", exc)
            return {"ok": False, "error": str(exc), "text": text, "backend": self._backend}
