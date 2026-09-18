"""Streaming / cancellable TTS playback controller."""
from __future__ import annotations

import logging
import subprocess
import threading
from typing import Any, Callable

from .speech_synthesizer import SpeechSynthesizer

logger = logging.getLogger(__name__)


class StreamingTTS:
    def __init__(self, synthesizer: SpeechSynthesizer | None = None) -> None:
        self.synth = synthesizer or SpeechSynthesizer()
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._speaking = False
        self.on_started: Callable[[], None] | None = None
        self.on_completed: Callable[[], None] | None = None
        self.on_cancelled: Callable[[], None] | None = None

    @property
    def speaking(self) -> bool:
        return self._speaking

    def speak(self, text: str, *, blocking: bool = False) -> dict[str, Any]:
        self.cancel()
        self._cancel.clear()
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty"}

        def _run() -> None:
            self._speaking = True
            if self.on_started:
                try:
                    self.on_started()
                except Exception:
                    pass
            try:
                # Prefer streaming OS say for barge-in cancel via kill
                import shutil

                if shutil.which("say") and not self._cancel.is_set():
                    self._proc = subprocess.Popen(["say", text])
                    self._proc.wait()
                else:
                    self.synth.synthesize(text)
            finally:
                cancelled = self._cancel.is_set()
                self._speaking = False
                self._proc = None
                cb = self.on_cancelled if cancelled else self.on_completed
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass

        if blocking:
            _run()
            return {"ok": True, "blocking": True}
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        return {"ok": True, "blocking": False}

    def cancel(self) -> None:
        self._cancel.set()
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self._speaking = False

    def stop(self) -> None:
        self.cancel()

    def status(self) -> dict[str, Any]:
        return {"speaking": self._speaking, "synth": self.synth.status()}
