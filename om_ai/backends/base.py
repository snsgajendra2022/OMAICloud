from __future__ import annotations

from typing import Any, Generator, Protocol, runtime_checkable


class NativeCheckpointError(RuntimeError):
    """Raised when OM native backend is selected but no real checkpoint is available."""

    def __init__(self, message: str = "OM-1.0 checkpoint unavailable."):
        super().__init__(message)


@runtime_checkable
class ModelBackend(Protocol):
    """Pluggable inference backend protocol for OM chat / generate."""

    def generate(self, prompt: str, **kwargs: Any) -> str: ...

    def chat(self, messages: list[dict], **kwargs: Any) -> str: ...

    def stream_chat(
        self, messages: list[dict], **kwargs: Any
    ) -> Generator[str, None, None]: ...

    def health(self) -> dict[str, Any]: ...

    def model_info(self) -> dict[str, Any]: ...
