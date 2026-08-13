"""OpenAI-compatible API shim for OpenClaw / OpenAI SDK clients.

Exposes:
  GET  /api/v1/models
  GET  /api/v1/chat/backend
  POST /api/v1/chat/completions
  POST /api/v1/completions

Routes chat to OM native / Ollama / OpenAI-compatible APIs / local OM engine based on
``OM_AI_CHAT_BACKEND`` / ``OM_MODEL_PROVIDER`` (see ``om_ai.runtime.chat_backend``).
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth, require_permission
from om_ai.backends.base import NativeCheckpointError
from om_ai.runtime.chat_backend import backend_status, chat_reply, configured_backend, resolve_backend
from om_ai.security.auth import TenantContext

router = APIRouter(prefix="/api/v1", tags=["OpenAI Compatible"])

# Filled by main.py after engine singleton exists
_engine = None
_native_backend = None
_default_model_id = "om-tiny"


def bind_engine(
    engine,
    default_model_id: str = "om-tiny",
    native_backend=None,
) -> None:
    global _engine, _default_model_id, _native_backend
    _engine = engine
    _default_model_id = default_model_id
    _native_backend = native_backend


def _local_loaded() -> bool:
    return bool(_engine is not None and getattr(_engine, "model", None) is not None)


def _native_ready() -> bool:
    nb = _native_backend
    return bool(nb is not None and getattr(nb, "loaded", False) and getattr(nb, "_trained", False))


def _require_local_engine():
    if not _local_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OM model not loaded. Start server with OM_AI_AUTOLOAD=1 "
                "or POST /v1/model/load first. "
                "Default is OM-1.0 native (OM_MODEL_PROVIDER=om_native) with a "
                "checkpoint. Alternatives: OM_AI_OPENAI_API_KEY / OPENAI_API_KEY, "
                "or explicit OM_AI_CHAT_BACKEND=ollama."
            ),
        )
    return _engine


class ChatMessage(BaseModel):
    role: str
    content: str | list[Any] | None = ""


class ChatCompletionsRequest(BaseModel):
    model: str = Field(default="om-tiny")
    messages: list[ChatMessage]
    temperature: float | None = 0.8
    top_p: float | None = 1.0
    max_tokens: int | None = Field(default=128, ge=1, le=4096)
    stream: bool = False
    stop: str | list[str] | None = None
    frequency_penalty: float | None = 0.0
    presence_penalty: float | None = 0.0
    n: int | None = 1
    user: str | None = None


class CompletionsRequest(BaseModel):
    model: str = Field(default="om-tiny")
    prompt: str | list[str]
    temperature: float | None = 0.8
    top_p: float | None = 1.0
    max_tokens: int | None = Field(default=128, ge=1, le=4096)
    stream: bool = False
    stop: str | list[str] | None = None


def _normalize_content(content: str | list[Any] | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # OpenAI multimodal content parts
    parts = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif "text" in item:
                parts.append(str(item["text"]))
        else:
            parts.append(str(item))
    return "\n".join(p for p in parts if p)


def _messages_to_dicts(messages: list[ChatMessage]) -> list[dict]:
    out = []
    for m in messages:
        out.append({"role": m.role, "content": _normalize_content(m.content)})
    return out


def _chat_response(
    model: str,
    text: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    *,
    backend: str | None = None,
    provider: str | None = None,
) -> dict:
    body: dict[str, Any] = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    if backend:
        body["om_backend"] = backend
    if provider:
        body["om_provider"] = provider
    return body


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_chat(
    messages: list[dict],
    *,
    max_new: int,
    temperature: float,
    top_p: float,
) -> tuple[str, str, str, str]:
    """Return (text, response_model_id, backend_name, provider)."""
    info = resolve_backend(local_loaded=_local_loaded(), native_ready=_native_ready())
    try:
        text, used = chat_reply(
            messages,
            local_chat=_engine.chat if _engine is not None else None,
            local_loaded=_local_loaded(),
            native_chat=_native_backend.chat if _native_backend is not None else None,
            native_ready=_native_ready(),
            max_new_tokens=max_new,
            temperature=temperature,
            top_p=top_p,
        )
    except NativeCheckpointError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "OM-1.0 checkpoint unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    model_name = used.model or info.model or _default_model_id
    if used.backend == "om_native":
        model_name = "OM-1.0"
    return text, model_name, used.backend, used.provider or ""


@router.get("/chat/backend")
def chat_backend_info(ctx: TenantContext = Depends(require_auth)):
    """Report which chat backend is active (om_native / local / ollama / openai)."""
    return backend_status(local_loaded=_local_loaded(), native_ready=_native_ready())


@router.get("/models")
def list_models(ctx: TenantContext = Depends(require_auth)):
    eng = _engine
    loaded = bool(eng and getattr(eng, "model", None) is not None)
    info = resolve_backend(local_loaded=loaded, native_ready=_native_ready())
    if info.backend == "om_native":
        return {
            "object": "list",
            "data": [
                {
                    "id": "OM-1.0",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "OM AI",
                    "permission": [],
                    "root": "OM-1.0",
                    "parent": None,
                    "loaded": _native_ready(),
                    "om_backend": "om_native",
                    "provider": "OM AI",
                    "backend_label": "OM Native",
                }
            ],
            "om_backend": "om_native",
            "provider": "OM AI",
        }

    models = [
        {
            "id": _default_model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "om-ai",
            "permission": [],
            "root": _default_model_id,
            "parent": None,
            "loaded": loaded,
            "om_backend": info.backend,
        }
    ]
    # Aliases clients may already have configured (OpenClaw / OpenRouter-style ids)
    for alias in (
        "om:free",
        "om-tiny",
        "om-ai",
        "local",
        info.model,
    ):
        if alias and alias != _default_model_id and all(m["id"] != alias for m in models):
            models.append(
                {
                    "id": alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "om-ai",
                    "permission": [],
                    "root": _default_model_id,
                    "parent": None,
                    "om_backend": info.backend,
                    "note": f"Alias mapped via {info.backend} backend",
                }
            )
    return {"object": "list", "data": models, "om_backend": info.backend}


@router.post("/chat/completions")
async def chat_completions(
    req: ChatCompletionsRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    messages = _messages_to_dicts(req.messages)
    max_new = int(req.max_tokens or 128)
    temperature = float(req.temperature if req.temperature is not None else 0.8)
    top_p = float(req.top_p if req.top_p is not None else 1.0)

    # When native is forced and checkpoint missing, fail fast with 503 (no Ollama).
    if configured_backend() == "om_native" and not _native_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OM-1.0 checkpoint unavailable.",
        )

    if req.stream:
        async def event_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "OM-1.0" if configured_backend() == "om_native" else (req.model or _default_model_id),
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": ""},
                            "finish_reason": None,
                        }
                    ],
                }
            )
            try:
                text, model_name, backend, provider = _run_chat(
                    messages,
                    max_new=max_new,
                    temperature=temperature,
                    top_p=top_p,
                )
            except HTTPException as exc:
                yield _sse({"error": {"message": str(exc.detail), "type": "server_error"}})
                yield "data: [DONE]\n\n"
                return
            except Exception as exc:
                yield _sse({"error": {"message": str(exc), "type": "server_error"}})
                yield "data: [DONE]\n\n"
                return

            step = max(1, len(text) // 20) if text else 1
            for i in range(0, len(text), step):
                piece = text[i : i + step]
                yield _sse(
                    {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model_name,
                        "om_backend": backend,
                        "om_provider": provider,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": piece},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "om_backend": backend,
                    "om_provider": provider,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    text, model_name, backend, provider = _run_chat(
        messages,
        max_new=max_new,
        temperature=temperature,
        top_p=top_p,
    )
    return _chat_response(model_name, text, backend=backend, provider=provider)


@router.post("/completions")
async def completions(
    req: CompletionsRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    if configured_backend() == "om_native" and not _native_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OM-1.0 checkpoint unavailable.",
        )
    eng = _require_local_engine()
    prompt = req.prompt if isinstance(req.prompt, str) else "\n".join(req.prompt)
    max_new = int(req.max_tokens or 128)
    temperature = float(req.temperature if req.temperature is not None else 0.8)
    top_p = float(req.top_p if req.top_p is not None else 1.0)
    model_name = "OM-1.0" if configured_backend() == "om_native" else (req.model or _default_model_id)
    try:
        text = eng.generate(
            prompt,
            max_new_tokens=max_new,
            temperature=temperature,
            top_p=top_p,
        )
        # Strip prompt echo if present
        if text.startswith(prompt):
            text = text[len(prompt) :]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": f"cmpl-{uuid.uuid4().hex[:24]}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "text": text,
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }
