"""OpenAI-compatible API shim for OpenClaw / OpenAI SDK clients.

Exposes:
  GET  /api/v1/models
  GET  /api/v1/chat/backend
  POST /api/v1/chat/completions
  POST /api/v1/completions

Routes chat to OM native (default) / OpenAI-compatible APIs / local OM engine based on
``OM_AI_CHAT_BACKEND`` / ``OM_MODEL_PROVIDER`` (see ``om_ai.runtime.chat_backend``).
Ollama is not part of the production path.
"""
from __future__ import annotations

import json
import logging
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
logger = logging.getLogger(__name__)

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


def _try_load_native() -> bool:
    """Lazy-load OM-1.0 if serve started before the checkpoint/tokenizer was ready."""
    if _native_ready():
        return True
    nb = _native_backend
    if nb is None:
        return False
    try:
        nb.ensure_loaded()
    except Exception:
        logger.exception("OM native lazy load failed")
        return False
    return _native_ready()


def _require_local_engine():
    if not _local_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OM model not loaded. Default is OM-1.0 native "
                "(OM_MODEL_PROVIDER=om_native) with a real checkpoint. "
                "Train with `om-ai train-om1`, or POST /v1/model/load. "
                "There is no Ollama fallback."
            ),
        )
    return _engine


class ChatMessage(BaseModel):
    role: str
    content: str | list[Any] | None = ""


class ChatCompletionsRequest(BaseModel):
    model: str = Field(default="om-tiny")
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    stream: bool = False
    stop: str | list[str] | None = None
    frequency_penalty: float | None = 0.0
    presence_penalty: float | None = 0.0
    n: int | None = 1
    user: str | None = None
    top_k: int | None = None
    repetition_penalty: float | None = None
    project_id: str | None = None
    conversation_id: str | None = None


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


def _resolve_project_context(
    *,
    tenant_id: str,
    actor: str,
    project_id: str | None = None,
    conversation_id: str | None = None,
) -> tuple[str | None, str]:
    """Return (project_id, project_instructions)."""
    pid = (project_id or "").strip() or None
    if not pid and conversation_id:
        try:
            from om_ai.api.conversations import get_bound_conversation_store

            store = get_bound_conversation_store()
            if store is not None:
                conv = store.get_conversation(conversation_id, tenant_id, actor)
                pid = getattr(conv, "project_id", None) or None
        except Exception:
            pid = None
    if not pid:
        return None, ""
    try:
        from om_ai.api.workspace_store import get_workspace_store

        proj = get_workspace_store().get_project(pid, tenant_id, actor)
        instructions = str(proj.get("instructions") or "").strip()
        if not instructions:
            try:
                from om_ai.api.platform_store import get_platform_store

                versions = get_platform_store().list_instruction_versions(
                    tenant_id, actor, owner_type="project", owner_id=pid
                )
                if versions:
                    instructions = str(versions[0].get("content") or "").strip()
            except Exception:
                pass
        return pid, instructions
    except Exception:
        return pid, ""


def _run_chat(
    messages: list[dict],
    *,
    max_new: int | None,
    temperature: float | None,
    top_p: float | None,
    top_k: int | None = None,
    repetition_penalty: float | None = None,
    tenant_id: str = "default",
    actor: str = "",
    project_id: str | None = None,
    project_instructions: str = "",
    model: str | None = None,
) -> tuple[str, str, str, str]:
    """Return (text, response_model_id, backend_name, provider)."""
    info = resolve_backend(local_loaded=_local_loaded(), native_ready=_native_ready())
    settings: dict = {}
    try:
        from om_ai.api.platform_store import get_platform_store
        from om_ai.runtime.session_flags import apply_session_flags, flags_from_settings

        settings = get_platform_store().get_settings(tenant_id, actor or "")
        if settings.get("llm_enabled") is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="LLM is disabled in Settings → AI. Turn on Enable LLM to chat.",
            )
        flag_ctx = apply_session_flags(flags_from_settings(settings))
    except HTTPException:
        raise
    except Exception:
        from contextlib import nullcontext

        flag_ctx = nullcontext()
        settings = {}

    # External LLM path (user-enabled connectors)
    try:
        from om_ai.runtime.external_llms import (
            chat_external,
            normalize_provider_id,
            provider_ready,
        )

        pid = normalize_provider_id(model)
        if pid and pid != "om":
            enabled = settings.get("llm_providers") or {}
            stored_keys = settings.get("llm_api_keys") or {}
            ok, reason = provider_ready(pid, enabled=enabled, stored_keys=stored_keys)
            if not ok:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
            with flag_ctx:
                text, display, vendor = chat_external(
                    pid,
                    messages,
                    stored_keys=stored_keys,
                    max_tokens=int(max_new or 1024),
                    temperature=float(temperature if temperature is not None else 0.7),
                    top_p=float(top_p if top_p is not None else 1.0),
                )
            return text, display, "external", vendor
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        with flag_ctx:
            text, used = chat_reply(
                messages,
                local_chat=_engine.chat if _engine is not None else None,
                local_loaded=_local_loaded(),
                native_chat=_native_backend.chat if _native_backend is not None else None,
                native_ready=_native_ready(),
                max_new_tokens=max_new,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                tenant_id=tenant_id,
                actor=actor,
                project_id=project_id,
                project_instructions=project_instructions,
                model=model,
            )
    except NativeCheckpointError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "OM-1.0 checkpoint unavailable.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    model_name = used.model or info.model or _default_model_id
    if used.backend == "om_native" and not model:
        model_name = "OM-L1"
    return text, model_name, used.backend, used.provider or ""


@router.get("/chat/backend")
def chat_backend_info(ctx: TenantContext = Depends(require_auth)):
    """Report which chat backend is active (om_native / local / openai)."""
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
    max_new = int(req.max_tokens) if req.max_tokens is not None else None
    temperature = float(req.temperature) if req.temperature is not None else None
    top_p = float(req.top_p) if req.top_p is not None else None
    top_k = int(req.top_k) if req.top_k is not None else None
    repetition_penalty = (
        float(req.repetition_penalty) if req.repetition_penalty is not None else None
    )
    project_id, project_instructions = _resolve_project_context(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        project_id=req.project_id,
        conversation_id=req.conversation_id,
    )

    from om_ai.runtime.external_llms import normalize_provider_id

    ext_pid = normalize_provider_id(req.model)
    use_external = bool(ext_pid and ext_pid != "om")

    # Retry native load (checkpoint may have appeared after serve start).
    # If still not ready, continue — chat_reply uses the cognitive brain
    # instead of a third-party LLM. Raw generate (/completions) still needs weights.
    if not use_external and configured_backend() == "om_native":
        _try_load_native()

    chat_kwargs = dict(
        max_new=max_new,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        project_id=project_id,
        project_instructions=project_instructions,
        model=req.model,
    )

    if req.stream:
        async def event_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": req.model or ("OM-1.0" if configured_backend() == "om_native" else _default_model_id),
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
                text, model_name, backend, provider = _run_chat(messages, **chat_kwargs)
            except HTTPException as exc:
                yield _sse({"error": {"message": str(exc.detail), "type": "server_error"}})
                yield "data: [DONE]\n\n"
                return
            except Exception as exc:
                yield _sse({"error": {"message": str(exc), "type": "server_error"}})
                yield "data: [DONE]\n\n"
                return

            step = 2 if text else 1
            for i in range(0, len(text), step):
                piece = text[i : i + step]
                yield _sse(
                    {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model_name,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": piece},
                                "finish_reason": None,
                            }
                        ],
                        "om_backend": backend,
                        "om_provider": provider,
                    }
                )
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {"index": 0, "delta": {}, "finish_reason": "stop"}
                    ],
                    "om_backend": backend,
                    "om_provider": provider,
                }
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    text, model_name, backend, provider = _run_chat(messages, **chat_kwargs)
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
