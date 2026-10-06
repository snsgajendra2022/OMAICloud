from __future__ import annotations

import logging
from typing import Any

from .generation_config import GenerationConfig
from .generation_result import GenerationResult

logger = logging.getLogger(__name__)


class ModelGateway:
    """
    Single canonical entry point for OM model generation.

    Every higher-level component should use this gateway instead
    of calling OMNativeBackend / LocalLLMEngine directly.
    """

    def __init__(self, backend: Any | None = None) -> None:
        self._backend = backend

    def _resolve_backend(self) -> Any:
        if self._backend is not None:
            return self._backend

        from om_ai.api import main as api_main

        backend = getattr(api_main, "native_backend", None)

        if backend is None:
            raise RuntimeError("OM native backend is unavailable")

        self._backend = backend
        return backend

    def generate(
        self,
        prompt: str,
        *,
        config: GenerationConfig | None = None,
        context: dict[str, Any] | None = None,
    ) -> GenerationResult:

        prompt = str(prompt or "").strip()

        if not prompt:
            return GenerationResult(
                text="",
                success=False,
                reason="empty_prompt",
            )

        cfg = config or GenerationConfig()

        try:
            backend = self._resolve_backend()

            text = self._call_backend(
                backend,
                prompt,
                cfg,
                context or {},
            )

            text = self._clean(text)

            if not text:
                return GenerationResult(
                    text="",
                    success=False,
                    rejected=True,
                    reason="empty_generation",
                )

            quality, reason = self._quality(text)

            if quality <= 0:
                return GenerationResult(
                    text="",
                    success=False,
                    rejected=True,
                    quality=quality,
                    reason=reason,
                )

            return GenerationResult(
                text=text,
                success=True,
                quality=quality,
                metadata={
                    "backend": type(backend).__name__,
                    "temperature": cfg.temperature,
                },
            )

        except Exception as exc:
            logger.exception("OM generation failed")

            return GenerationResult(
                text="",
                success=False,
                rejected=True,
                reason=f"{type(exc).__name__}: {exc}",
            )

    def _call_backend(
        self,
        backend: Any,
        prompt: str,
        config: GenerationConfig,
        context: dict[str, Any],
    ) -> str:

        messages = [
            {
                "role": "system",
                "content": (
                    "You are OM, a capable conversational AI. "
                    "Understand the user's actual intent before answering. "
                    "Respond naturally, clearly and directly."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        chat = getattr(backend, "chat", None)

        if callable(chat):
            try:
                result = chat(
                    messages,
                    **config.to_kwargs(),
                )
            except TypeError:
                result = chat(messages)

            return self._extract_text(result)

        generate = getattr(backend, "generate", None)

        if callable(generate):
            result = generate(
                prompt,
                **config.to_kwargs(),
            )

            return self._extract_text(result)

        raise RuntimeError(
            f"Backend {type(backend).__name__} has no chat/generate method"
        )

    @staticmethod
    def _extract_text(result: Any) -> str:
        if result is None:
            return ""

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            for key in (
                "answer",
                "text",
                "content",
                "response",
                "generated_text",
            ):
                value = result.get(key)

                if isinstance(value, str):
                    return value

        return str(result)

    @staticmethod
    def _clean(text: str) -> str:
        return (
            str(text or "")
            .replace("\x00", "")
            .strip()
        )

    @staticmethod
    def _quality(text: str) -> tuple[float, str | None]:
        if not text:
            return 0.0, "empty"

        replacement_count = text.count("\ufffd")

        if replacement_count:
            return 0.0, "tokenizer_replacement_character"

        if len(text) < 2:
            return 0.0, "too_short"

        # Detect obvious token/character corruption.
        alpha = sum(ch.isalpha() for ch in text)
        printable = sum(ch.isprintable() for ch in text)

        if printable / max(len(text), 1) < 0.85:
            return 0.0, "non_printable_output"

        if alpha == 0:
            return 0.0, "no_language_content"

        # Very long random-looking strings are rejected.
        words = text.split()

        if len(words) > 20:
            unique_ratio = len(set(words)) / len(words)

            if unique_ratio > 0.95 and len(text) > 500:
                return 0.0, "possible_corrupted_generation"

        return 1.0, None