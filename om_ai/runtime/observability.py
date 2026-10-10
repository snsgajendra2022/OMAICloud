"""Privacy-conscious request tracing for OM's runtime.

Tracing is opt-in via OM_TRACE_JSONL. Events intentionally exclude prompts,
model outputs, credentials, and arbitrary user-controlled payloads by default.
"""
from __future__ import annotations

import contextvars
import json
import inspect
import os
import threading
import time
import uuid
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Iterator

_TRACE_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("om_trace_id", default=None)
_REQUEST_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("om_request_id", default=None)
_CONVERSATION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("om_conversation_id", default=None)
_LOCK = threading.Lock()
_SAFE_FIELDS = {
    "model_id", "model_version", "tokenizer_version", "input_tokens",
    "output_tokens", "quality_score", "regeneration_count", "status",
    "error_type", "provider", "device", "retrieval_count", "tool_name",
}


def current_trace() -> dict[str, str | None]:
    """Return the trace identifiers currently bound to this execution context."""
    return {
        "trace_id": _TRACE_ID.get(),
        "request_id": _REQUEST_ID.get(),
        "conversation_id": _CONVERSATION_ID.get(),
    }


def _write_event(event: dict[str, Any]) -> None:
    destination = os.getenv("OM_TRACE_JSONL", "").strip()
    if not destination:
        return
    path = Path(destination).expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True, default=str) + "\n"
        with _LOCK:
            with path.open("a", encoding="utf-8") as stream:
                stream.write(line)
    except OSError:
        # Observability must not crash inference; deployment health checks should
        # separately alert when the configured trace sink is unwritable.
        return


@contextmanager
def trace_request(
    *,
    request_id: str | None = None,
    conversation_id: str | None = None,
    model_id: str | None = None,
    model_version: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[dict[str, str | None]]:
    """Bind request identifiers and emit start/end events without logging content."""
    trace_id = uuid.uuid4().hex
    req_id = str(request_id or uuid.uuid4().hex)
    tokens = (
        _TRACE_ID.set(trace_id),
        _REQUEST_ID.set(req_id),
        _CONVERSATION_ID.set(str(conversation_id) if conversation_id else None),
    )
    started = time.perf_counter()
    safe = {key: value for key, value in (attributes or {}).items() if key in _SAFE_FIELDS}
    base = {
        "trace_id": trace_id, "request_id": req_id,
        "conversation_id": str(conversation_id) if conversation_id else None,
        "model_id": model_id, "model_version": model_version,
    }
    _write_event({**base, "event": "request.start", "timestamp": time.time(), **safe})
    try:
        yield {key: value for key, value in base.items() if value is not None}
    except BaseException as exc:
        _write_event({
            **base, "event": "request.error", "timestamp": time.time(),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "error_type": type(exc).__name__,
        })
        raise
    else:
        _write_event({
            **base, "event": "request.end", "timestamp": time.time(),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            **safe,
        })
    finally:
        _CONVERSATION_ID.reset(tokens[2])
        _REQUEST_ID.reset(tokens[1])
        _TRACE_ID.reset(tokens[0])


@contextmanager
def trace_span(name: str, *, attributes: dict[str, Any] | None = None) -> Iterator[None]:
    """Measure one named stage inside the active request trace."""
    started = time.perf_counter()
    ids = current_trace()
    safe = {key: value for key, value in (attributes or {}).items() if key in _SAFE_FIELDS}
    _write_event({**ids, "event": "span.start", "span": str(name), "timestamp": time.time(), **safe})
    try:
        yield
    except BaseException as exc:
        _write_event({
            **ids, "event": "span.error", "span": str(name), "timestamp": time.time(),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "error_type": type(exc).__name__,
        })
        raise
    else:
        _write_event({
            **ids, "event": "span.end", "span": str(name), "timestamp": time.time(),
            "duration_ms": round((time.perf_counter() - started) * 1000, 3), **safe,
        })


def trace_function(name: str):
    """Decorator for synchronous runtime entrypoints; never captures input text."""
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            nested = kwargs.get("kwargs")
            nested = nested if isinstance(nested, dict) else {}
            conversation_id = kwargs.get("conversation_id") or nested.get("conversation_id")
            request_id = kwargs.get("request_id")
            with trace_request(
                request_id=str(request_id) if request_id else None,
                conversation_id=str(conversation_id) if conversation_id else None,
            ):
                with trace_span(name):
                    return function(*args, **kwargs)
        return wrapped
    return decorate


def trace_operation(name: str):
    """Trace a sync method or generator without creating a nested request ID."""
    def decorate(function):
        if inspect.isgeneratorfunction(function):
            @wraps(function)
            def generator_wrapped(*args, **kwargs):
                with trace_span(name):
                    yield from function(*args, **kwargs)
            return generator_wrapped

        @wraps(function)
        def wrapped(*args, **kwargs):
            with trace_span(name):
                return function(*args, **kwargs)
        return wrapped
    return decorate
