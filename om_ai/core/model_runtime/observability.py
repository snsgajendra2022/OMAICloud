"""Observability and tracing for model generation in production."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import time
from typing import Any
import uuid

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class GenerationTrace:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: str = "OM-1.0"
    checkpoint: str = ""
    tokenizer: str = ""
    route: str = "canonical_gateway"
    generation_time_ms: float = 0.0
    tokens: int = 0
    temperature: float = 0.7
    context_length: int = 0
    quality_score: float = 0.0
    fallback_used: bool = False
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "checkpoint": self.checkpoint,
            "tokenizer": self.tokenizer,
            "route": self.route,
            "generation_time_ms": self.generation_time_ms,
            "tokens": self.tokens,
            "temperature": self.temperature,
            "context_length": self.context_length,
            "quality_score": self.quality_score,
            "fallback_used": self.fallback_used,
            "error": self.error,
            "created_at": self.created_at,
        }


class GenerationTracer:
    """Collects and logs generation traces for production monitoring."""

    def __init__(self) -> None:
        self._traces: list[GenerationTrace] = []

    def record(self, trace: GenerationTrace) -> None:
        self._traces.append(trace)
        if len(self._traces) > 1000:
            self._traces = self._traces[-1000:]
        if trace.error:
            logger.warning("Generation trace error [%s]: %s", trace.request_id, trace.error)
        else:
            logger.info(
                "Generation trace [%s]: model=%s, route=%s, time=%.1fms, quality=%.2f",
                trace.request_id,
                trace.model,
                trace.route,
                trace.generation_time_ms,
                trace.quality_score,
            )

    @property
    def recent_traces(self) -> list[GenerationTrace]:
        return list(self._traces)


_GLOBAL_TRACER: GenerationTracer | None = None


def get_tracer() -> GenerationTracer:
    global _GLOBAL_TRACER
    if _GLOBAL_TRACER is None:
        _GLOBAL_TRACER = GenerationTracer()
    return _GLOBAL_TRACER
