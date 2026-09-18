"""Cancellation tokens for companion sessions."""
from __future__ import annotations

import threading
import uuid


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise RuntimeError("operation cancelled")


class CancellationManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokens: dict[str, CancellationToken] = {}

    def create(self, session_id: str | None = None) -> tuple[str, CancellationToken]:
        sid = session_id or str(uuid.uuid4())
        token = CancellationToken()
        with self._lock:
            self._tokens[sid] = token
        return sid, token

    def get(self, session_id: str) -> CancellationToken | None:
        with self._lock:
            return self._tokens.get(session_id)

    def cancel(self, session_id: str) -> bool:
        token = self.get(session_id)
        if token is None:
            return False
        token.cancel()
        return True
