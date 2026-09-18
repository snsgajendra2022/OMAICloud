"""Microphone streaming with reconnect."""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from .audio_buffer import AudioBuffer
from .audio_device import AudioDeviceManager

logger = logging.getLogger(__name__)


class AudioStream:
    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        blocksize: int = 1024,
        device_manager: AudioDeviceManager | None = None,
        on_chunk: Callable[[Any], None] | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.devices = device_manager or AudioDeviceManager()
        self.on_chunk = on_chunk
        self.buffer = AudioBuffer(sample_rate=sample_rate)
        self._stream = None
        self._lock = threading.RLock()
        self._running = False
        self._error: str | None = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._running:
                return {"ok": True, "already": True}
            try:
                import sounddevice as sd  # type: ignore

                device = self.devices.selected_input()

                def _callback(indata, frames, time, status):  # noqa: ARG001
                    if status:
                        logger.debug("audio status: %s", status)
                    mono = indata[:, 0] if indata.ndim > 1 else indata.reshape(-1)
                    self.buffer.extend(mono)
                    if self.on_chunk:
                        try:
                            self.on_chunk(mono.copy())
                        except Exception as exc:
                            logger.debug("on_chunk error: %s", exc)

                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.blocksize,
                    channels=1,
                    dtype="float32",
                    device=device,
                    callback=_callback,
                )
                self._stream.start()
                self._running = True
                self._error = None
                return {"ok": True, "sample_rate": self.sample_rate, "device": device}
            except Exception as exc:
                self._error = str(exc)
                self._running = False
                logger.warning("AudioStream start failed: %s", exc)
                return {"ok": False, "error": str(exc)}

    def stop(self) -> None:
        with self._lock:
            self._running = False
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

    def reconnect(self) -> dict[str, Any]:
        self.stop()
        return self.start()

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "error": self._error,
            "buffered_seconds": self.buffer.duration(),
            "sample_rate": self.sample_rate,
        }
