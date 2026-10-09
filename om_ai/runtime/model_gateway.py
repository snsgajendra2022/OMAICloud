"""Canonical native-model gateway used by OM application entry points.

The gateway deliberately fails closed. It never manufactures answer text, and it
keeps embedding capability explicit until a trained embedding model is configured.
"""
from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any


class ModelGatewayError(RuntimeError):
    """A native model operation failed or returned unusable output."""


class ModelGateway:
    """Single native inference contract for generate, chat and streaming."""

    def __init__(self, backend: Any):
        self.backend = backend

    def health(self) -> dict[str, Any]:
        return self.backend.health()

    def _require_ready(self) -> None:
        health = self.health()
        if not health.get("ok"):
            raise ModelGatewayError(
                "OM native model is not ready; load a compatible checkpoint and tokenizer first."
            )

    @staticmethod
    def _validate_text(text: Any, *, operation: str) -> str:
        from om_ai.runtime.engine import is_degenerate_generation, usable_generation_text

        cleaned = usable_generation_text(str(text or ""))
        if not cleaned:
            raise ModelGatewayError(f"OM native {operation} returned no usable text.")
        if is_degenerate_generation(cleaned):
            raise ModelGatewayError(f"OM native {operation} failed the output-integrity check.")
        return cleaned

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        self._require_ready()
        try:
            return self._validate_text(
                self.backend.generate(prompt, **kwargs), operation="generation"
            )
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError("OM native generation failed.") from exc

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        self._require_ready()
        try:
            return self._validate_text(
                self.backend.chat(messages, **kwargs), operation="chat"
            )
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError("OM native chat failed.") from exc

    def stream_generate(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        self._require_ready()
        try:
            yield from self.backend.generate_stream(prompt, **kwargs)
        except Exception as exc:
            raise ModelGatewayError("OM native streaming generation failed.") from exc

    def stream_chat(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> Iterator[str]:
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        self._require_ready()
        try:
            chunks: Iterable[str] = self.backend.stream_chat(messages, **kwargs)
            for chunk in chunks:
                if chunk:
                    yield str(chunk)
        except Exception as exc:
            raise ModelGatewayError("OM native streaming failed.") from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embedding is intentionally unavailable without a trained embedder."""
        if not isinstance(texts, list) or not texts or any(
            not isinstance(item, str) or not item.strip() for item in texts
        ):
            raise ValueError("texts must be a non-empty list of non-empty strings")
        raise NotImplementedError(
            "OM has no certified native embedding model configured; refusing to return fake vectors."
        )
