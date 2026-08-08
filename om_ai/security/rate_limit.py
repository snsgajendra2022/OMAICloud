"""In-memory sliding-window rate limiter for OM AI."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class _Window:
    """Per-key sliding window of request timestamps."""
    timestamps: deque[float] = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)


class RateLimiter:
    """Thread-safe sliding-window rate limiter (requests per window).

    Each unique *key* (e.g. API key, IP address, tenant ID) gets its own
    independent window tracked in memory.

    Example::

        limiter = RateLimiter(max_requests=60, window_seconds=60)
        try:
            limiter.check("user:alice")
        except RateLimitExceeded:
            # return HTTP 429
            ...

    The object is thread-safe and suitable for use with ASGI / FastAPI.
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: float = 60.0,
    ) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._windows: dict[str, _Window] = {}
        self._global_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_window(self, key: str) -> _Window:
        with self._global_lock:
            if key not in self._windows:
                self._windows[key] = _Window()
            return self._windows[key]

    def _evict(self, window: _Window, now: float) -> None:
        """Remove timestamps older than the window (must hold window.lock)."""
        cutoff = now - self._window_seconds
        while window.timestamps and window.timestamps[0] <= cutoff:
            window.timestamps.popleft()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, key: str) -> None:
        """Record a request for *key*; raise RateLimitExceeded if over budget.

        This method both checks the current count *and* records the call in
        one atomic operation.
        """
        now = time.monotonic()
        window = self._get_window(key)

        with window.lock:
            self._evict(window, now)
            if len(window.timestamps) >= self._max_requests:
                oldest = window.timestamps[0]
                retry_after = self._window_seconds - (now - oldest)
                raise RateLimitExceeded(
                    key=key,
                    max_requests=self._max_requests,
                    window_seconds=self._window_seconds,
                    retry_after=max(0.0, retry_after),
                )
            window.timestamps.append(now)

    def remaining(self, key: str) -> int:
        """Return how many requests *key* can still make in the current window."""
        now = time.monotonic()
        window = self._get_window(key)
        with window.lock:
            self._evict(window, now)
            return max(0, self._max_requests - len(window.timestamps))

    def reset(self, key: str) -> None:
        """Clear the rate-limit state for *key* (e.g. for testing)."""
        window = self._get_window(key)
        with window.lock:
            window.timestamps.clear()

    def purge_stale(self) -> int:
        """Remove windows for keys that have had no activity in the last window.

        Returns the number of windows purged. Call periodically to release memory.
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds
        purged = 0
        with self._global_lock:
            stale = [
                k for k, w in self._windows.items()
                if not w.timestamps or w.timestamps[-1] <= cutoff
            ]
            for k in stale:
                del self._windows[k]
                purged += 1
        return purged

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> float:
        return self._window_seconds


class RateLimitExceeded(Exception):
    """Raised when a key exceeds its allocated request budget."""

    def __init__(
        self,
        key: str,
        max_requests: int,
        window_seconds: float,
        retry_after: float,
    ) -> None:
        super().__init__(
            f"Rate limit exceeded for '{key}': "
            f"max {max_requests} requests per {window_seconds}s. "
            f"Retry after {retry_after:.1f}s."
        )
        self.key = key
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.retry_after = retry_after
