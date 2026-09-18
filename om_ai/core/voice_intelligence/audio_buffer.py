"""Bounded PCM audio buffer."""
from __future__ import annotations

from collections import deque
from typing import Deque
import numpy as np


class AudioBuffer:
    def __init__(self, *, max_seconds: float = 30.0, sample_rate: int = 16000) -> None:
        self.sample_rate = int(sample_rate)
        self.max_samples = int(max_seconds * self.sample_rate)
        self._buf: Deque[float] = deque(maxlen=self.max_samples)

    def extend(self, samples) -> None:
        arr = np.asarray(samples, dtype=np.float32).reshape(-1)
        self._buf.extend(arr.tolist())

    def clear(self) -> None:
        self._buf.clear()

    def size(self) -> int:
        return len(self._buf)

    def duration(self) -> float:
        return len(self._buf) / float(self.sample_rate or 1)

    def numpy(self) -> "np.ndarray":
        if not self._buf:
            return np.zeros(0, dtype=np.float32)
        return np.asarray(self._buf, dtype=np.float32)

    def snapshot_seconds(self, seconds: float) -> "np.ndarray":
        n = int(seconds * self.sample_rate)
        data = self.numpy()
        if data.size <= n:
            return data
        return data[-n:]
