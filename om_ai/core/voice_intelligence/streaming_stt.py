"""Incremental STT over rolling audio windows."""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

import numpy as np

from .speech_recognizer import SpeechRecognizer


class StreamingSTT:
    def __init__(
        self,
        recognizer: SpeechRecognizer | None = None,
        *,
        sample_rate: int = 16000,
        window_seconds: float = 2.0,
        on_partial: Callable[[dict[str, Any]], None] | None = None,
        on_final: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.recognizer = recognizer or SpeechRecognizer()
        self.sample_rate = sample_rate
        self.window_seconds = window_seconds
        self.on_partial = on_partial
        self.on_final = on_final
        self._cancel = threading.Event()
        self._buf = np.zeros(0, dtype=np.float32)
        self._lock = threading.RLock()

    def cancel(self) -> None:
        self._cancel.set()

    def reset(self) -> None:
        self._cancel.clear()
        with self._lock:
            self._buf = np.zeros(0, dtype=np.float32)

    def push(self, samples) -> dict[str, Any] | None:
        if self._cancel.is_set():
            return None
        arr = np.asarray(samples, dtype=np.float32).reshape(-1)
        with self._lock:
            self._buf = np.concatenate([self._buf, arr])
            need = int(self.window_seconds * self.sample_rate)
            if self._buf.size < need:
                return None
            window = self._buf[-need:]
        result = self.recognizer.transcribe_array(window, sample_rate=self.sample_rate)
        result["partial"] = True
        result["timestamp"] = time.time()
        if self.on_partial and result.get("text"):
            self.on_partial(result)
        return result

    def finalize(self) -> dict[str, Any]:
        with self._lock:
            audio = self._buf.copy()
            self._buf = np.zeros(0, dtype=np.float32)
        result = self.recognizer.transcribe_array(audio, sample_rate=self.sample_rate)
        result["partial"] = False
        result["final"] = True
        result["timestamp"] = time.time()
        if self.on_final:
            self.on_final(result)
        return result

    def status(self) -> dict[str, Any]:
        return {"recognizer": self.recognizer.status(), "cancelled": self._cancel.is_set()}
