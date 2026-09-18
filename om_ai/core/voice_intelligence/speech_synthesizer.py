"""TTS provider abstraction with graceful fallbacks."""
from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SpeechSynthesizer:
    def __init__(self) -> None:
        self._backend = "none"
        self._error: str | None = None
        self._detect()

    def _detect(self) -> None:
        if shutil.which("say"):
            self._backend = "macos_say"
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

    @property
    def ready(self) -> bool:
        return self._backend != "none"

    def status(self) -> dict[str, Any]:
        return {"backend": self._backend, "ready": self.ready, "error": self._error}

    def synthesize(self, text: str, *, output_path: str | Path | None = None) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty"}
        out = Path(output_path) if output_path else Path(tempfile.mkstemp(suffix=".aiff")[1])
        try:
            if self._backend == "macos_say":
                subprocess.run(["say", "-o", str(out), text], check=False, capture_output=True)
                return {"ok": out.exists(), "path": str(out), "backend": self._backend, "text": text}
            if self._backend == "pyttsx3":
                import pyttsx3

                eng = pyttsx3.init()
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
