"""OpenAI-compatible API shim for OpenClaw / OpenAI SDK clients.

Exposes:
  GET  /api/v1/models
  POST /api/v1/chat/completions
  POST /api/v1/completions

This does NOT call OpenAI. It routes to the local OM LocalLLMEngine.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncGenerator, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth, require_permission
from om_ai.security.auth import TenantContext

router = APIRouter(prefix="/api/v1", tags=["OpenAI Compatible"])

# Filled by main.py after engine singleton exists
_engine = None
_default_model_id = "om-tiny"


def bind_engine(engine, default_model_id: str = "om-tiny") -> None:
    global _engine, _default_model_id
    _engine = engine
    _default_model_id = default_model_id


def _require_engine():
    if _engine is None or getattr(_engine, "model", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OM model not loaded. Start server with OM_AI_AUTOLOAD=1 "
                "or POST /v1/model/load first."
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


def _chat_response(model: str, text: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> dict:
    return {
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


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/models")
def list_models(ctx: TenantContext = Depends(require_auth)):
    eng = _engine
    loaded = bool(eng and getattr(eng, "model", None) is not None)
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
        }
    ]
    # Aliases clients may already have configured (OpenClaw / OpenRouter-style ids)
    for alias in (
        "om:free",
        "om-tiny",
        "om-ai",
        "local",
    ):
        if alias != _default_model_id:
            models.append(
                {
                    "id": alias,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "om-ai",
                    "permission": [],
                    "root": _default_model_id,
                    "parent": None,
                    "note": f"Alias mapped to local {_default_model_id}",
                }
            )
    return {"object": "list", "data": models}


@router.post("/chat/completions")
async def chat_completions(
    req: ChatCompletionsRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    eng = _require_engine()
    messages = _messages_to_dicts(req.messages)
    max_new = int(req.max_tokens or 128)
    temperature = float(req.temperature if req.temperature is not None else 0.8)
    top_p = float(req.top_p if req.top_p is not None else 1.0)
    model_name = req.model or _default_model_id

    if req.stream:
        async def event_stream() -> AsyncGenerator[str, None]:
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            # role preamble
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": ""},
                            "finish_reason": None,
                        }
                    ],
                }
            )
            # Build prompt once, stream tokens from generate_stream via chat fallback
            # Use non-stream chat then fake stream if stream path is awkward for chat tokens
            try:
                text = eng.chat(
                    messages,
                    max_new_tokens=max_new,
                    temperature=temperature,
                    top_p=top_p,
                )
            except Exception as exc:
                yield _sse({"error": {"message": str(exc), "type": "server_error"}})
                yield "data: [DONE]\n\n"
                return

            # Emit in small chunks for client UX
            step = max(1, len(text) // 20) if text else 1
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
                    }
                )
            yield _sse(
                {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    try:
        text = eng.chat(
            messages,
            max_new_tokens=max_new,
            temperature=temperature,
            top_p=top_p,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _chat_response(model_name, text)


@router.post("/completions")
async def completions(
    req: CompletionsRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    eng = _require_engine()
    prompt = req.prompt if isinstance(req.prompt, str) else "\n".join(req.prompt)
    max_new = int(req.max_tokens or 128)
    temperature = float(req.temperature if req.temperature is not None else 0.8)
    top_p = float(req.top_p if req.top_p is not None else 1.0)
    model_name = req.model or _default_model_id
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
