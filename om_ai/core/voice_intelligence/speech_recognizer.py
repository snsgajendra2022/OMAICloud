"""STT backends: faster-whisper / whisper / existing voice hooks."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    def __init__(self, *, model_size: str = "base", language: str | None = "en") -> None:
        self.model_size = model_size
        self.language = language
        self._model = None
        self._backend = "none"
        self._init_error: str | None = None
        self._bootstrap()

    def _bootstrap(self) -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore

            self._model = WhisperModel(self.model_size, device="auto", compute_type="int8")
            self._backend = "faster_whisper"
            return
        except Exception as exc:
            self._init_error = f"faster_whisper:{exc}"
        try:
            import whisper  # type: ignore

            self._model = whisper.load_model(self.model_size)
            self._backend = "whisper"
            return
        except Exception as exc:
            self._init_error = f"{self._init_error}; whisper:{exc}"
        # Existing OM voice hook
        try:
            from om_ai.voice.speech_to_text import SpeechToText  # type: ignore

            self._model = SpeechToText()
            self._backend = "om_voice_stt"
        except Exception as exc:
            self._init_error = f"{self._init_error}; om_voice:{exc}"

    @property
    def ready(self) -> bool:
        return self._model is not None

    def status(self) -> dict[str, Any]:
        return {"backend": self._backend, "ready": self.ready, "error": self._init_error, "model_size": self.model_size}

    def transcribe_array(self, audio: np.ndarray, *, sample_rate: int = 16000) -> dict[str, Any]:
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        if audio.size == 0:
            return {"text": "", "ok": False, "reason": "empty_audio"}
        if self._backend == "faster_whisper" and self._model is not None:
            segments, info = self._model.transcribe(audio, language=self.language, vad_filter=True)
            parts = [s.text.strip() for s in segments if getattr(s, "text", None)]
            text = " ".join(parts).strip()
            return {
                "ok": bool(text),
                "text": text,
                "language": getattr(info, "language", self.language),
                "backend": self._backend,
                "confidence": float(getattr(info, "language_probability", 0.0) or 0.0),
            }
        if self._backend == "whisper" and self._model is not None:
            # whisper expects file or dict
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = Path(tmp.name)
            try:
                self._write_wav(path, audio, sample_rate)
                result = self._model.transcribe(str(path), language=self.language)
                text = str(result.get("text") or "").strip()
                return {"ok": bool(text), "text": text, "backend": self._backend, "confidence": 0.0}
            finally:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
        if self._backend == "om_voice_stt" and self._model is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = Path(tmp.name)
            try:
                self._write_wav(path, audio, sample_rate)
                if hasattr(self._model, "transcribe"):
                    text = str(self._model.transcribe(str(path)) or "").strip()
                else:
                    text = ""
                return {"ok": bool(text), "text": text, "backend": self._backend}
            finally:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
        return {"ok": False, "text": "", "reason": self._init_error or "stt_unavailable", "backend": self._backend}

    def _write_wav(self, path: Path, audio: np.ndarray, sample_rate: int) -> None:
        import wave
        import struct

        pcm = np.clip(audio, -1.0, 1.0)
        ints = (pcm * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(ints.tobytes())
