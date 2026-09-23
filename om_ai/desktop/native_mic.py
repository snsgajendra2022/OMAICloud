"""Native microphone bridge for desktop companion (when WebView mic is blocked)."""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class NativeMicBridge:
    """Capture mic in Python and emit final transcripts to a callback."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._on_text: Callable[[str], None] | None = None
        self._busy = False

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, on_text: Callable[[str], None]) -> dict[str, Any]:
        if self.running:
            self._on_text = on_text
            return {"ok": True, "already": True}
        self._on_text = on_text
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="om-native-mic", daemon=True)
        self._thread.start()
        return {"ok": True, "backend": self._probe_backend()}

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        return {"ok": True}

    def _probe_backend(self) -> str:
        try:
            import sounddevice  # noqa: F401

            from om_ai.core.voice_intelligence.speech_recognizer import SpeechRecognizer

            st = SpeechRecognizer(model_size="tiny").status()
            if st.get("ready"):
                return str(st.get("backend") or "whisper")
        except Exception:
            pass
        try:
            import speech_recognition  # noqa: F401

            return "speech_recognition"
        except Exception:
            return "none"

    def _loop(self) -> None:
        backend = self._probe_backend()
        if backend in {"faster_whisper", "whisper", "om_voice_stt"}:
            self._loop_whisper()
        elif backend == "speech_recognition":
            self._loop_speech_recognition()
        else:
            logger.warning(
                "Native mic: no STT backend. Install sounddevice+faster-whisper "
                "or speech_recognition, and allow Microphone for Terminal/Python."
            )
            # Idle until stop — UI may still use Chrome path
            while not self._stop.wait(1.0):
                pass

    def _loop_whisper(self) -> None:
        try:
            import sounddevice as sd
            import numpy as np
            from om_ai.core.voice_intelligence.speech_recognizer import SpeechRecognizer
        except Exception as exc:
            logger.warning("whisper mic loop unavailable: %s", exc)
            return

        rec = SpeechRecognizer(model_size="tiny", language=None)
        sr = 16000
        block = int(sr * 3.5)  # ~3.5s chunks
        while not self._stop.is_set():
            if self._busy:
                time.sleep(0.2)
                continue
            try:
                audio = sd.rec(block, samplerate=sr, channels=1, dtype="float32")
                sd.wait()
                flat = np.asarray(audio, dtype=np.float32).reshape(-1)
                rms = float(np.sqrt(np.mean(np.square(flat)))) if flat.size else 0.0
                if rms < 0.012:
                    continue
                out = rec.transcribe_array(flat, sample_rate=sr)
                text = str(out.get("text") or "").strip()
                if text and self._on_text:
                    self._on_text(text)
            except Exception as exc:
                logger.debug("native whisper chunk: %s", exc)
                time.sleep(0.5)

    def _loop_speech_recognition(self) -> None:
        try:
            import speech_recognition as sr
        except Exception as exc:
            logger.warning("speech_recognition unavailable: %s", exc)
            return

        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            try:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
            except Exception:
                pass
        while not self._stop.is_set():
            if self._busy:
                time.sleep(0.2)
                continue
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=8)
                try:
                    text = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    # Offline fallback
                    try:
                        text = recognizer.recognize_sphinx(audio)
                    except Exception:
                        continue
                text = str(text or "").strip()
                if text and self._on_text:
                    self._on_text(text)
            except Exception:
                time.sleep(0.3)

    def set_busy(self, busy: bool) -> None:
        self._busy = bool(busy)
