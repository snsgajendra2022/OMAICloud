"""OM AI Operating Brain — Production FastAPI application (v0.3.0)."""
from __future__ import annotations

import json
import logging
import os
import warnings
from pathlib import Path
from typing import AsyncGenerator

# Load repo ``.env`` into the process before any ``os.getenv`` below.
# Without this, values in ``.env`` are ignored unless the user ``source``s them.
from om_ai.env import load_dotenv

load_dotenv()

try:
    from om_ai.diagnostics.logging_setup import setup_logging

    setup_logging()
except Exception:
    pass

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from om_ai.agents import AgentOrchestrator
from om_ai.actions import SafeShellTool
from om_ai.actions.knowledge import KnowledgeSearchTool
from om_ai.discovery import OpenAPIDiscoveryTool
from om_ai.knowledge import PersistentKnowledgeBase
from om_ai.memory import SQLiteMemoryStore, ConversationStore
from om_ai.registry import ModelRegistry
from om_ai.backends import NativeCheckpointError, OMNativeBackend
from om_ai.backends.om_native import default_native_paths
from om_ai.runtime import LocalLLMEngine
from om_ai.runtime.chat_backend import configured_backend
from om_ai.security import (
    AuditLog,
    RateLimiter,
    RateLimitExceeded,
    SSRFGuard,
)
from om_ai.security.auth import TenantContext
from om_ai.api.deps import require_auth, require_permission
from om_ai.tenancy import TenantDirectory
from om_ai.api.conversations import router as conversations_router, bind_conversation_store
from om_ai.api.auth_routes import router as auth_router
from om_ai.api.workspace_routes import router as workspace_router
from om_ai.api.oi_routes import router as oi_router
from om_ai.api.platform_routes import router as platform_router
from om_ai.api.foundation_routes import router as foundation_router
from om_ai.continuous.feedback import FeedbackStore


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

_API_VERSION = "0.3.0"

app = FastAPI(
    title="OM AI Operating Brain",
    version=_API_VERSION,
    description=(
        "Self-hosted private AI platform. "
        "Default chat backend is OM-1.0 native (om_native) — no Ollama proxy."
    ),
)

# Optional CORS
_cors_origins = os.getenv("OM_AI_CORS_ORIGINS", "").strip()
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------

_DB_PATH = os.getenv("OM_AI_DB", "artifacts/om_ai.sqlite3")
_KB_PATH = os.getenv("OM_AI_KB", "artifacts/knowledge.sqlite3")
_AUDIT_DB = os.getenv("OM_AI_AUDIT_DB", "artifacts/audit.sqlite3")
_REGISTRY_ROOT = os.getenv("OM_AI_REGISTRY", "artifacts/registry")

engine = LocalLLMEngine()
native_backend = OMNativeBackend(engine=engine)
memory = SQLiteMemoryStore(_DB_PATH)
conversations = ConversationStore(_DB_PATH)
knowledge = PersistentKnowledgeBase(_KB_PATH)
registry = ModelRegistry(_REGISTRY_ROOT)
tenants = TenantDirectory()
audit_log = AuditLog(_AUDIT_DB)
_FEEDBACK_DB = os.getenv("OM_AI_FEEDBACK_DB", "artifacts/feedback.sqlite3")
feedback_store = FeedbackStore(_FEEDBACK_DB)

bind_conversation_store(conversations)
app.include_router(conversations_router)
app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(oi_router)
app.include_router(platform_router)
app.include_router(foundation_router)
_RATE_LIMIT_MAX = int(os.getenv("OM_AI_RATE_LIMIT", "120"))
rate_limiter = RateLimiter(
    max_requests=max(1, _RATE_LIMIT_MAX),
    window_seconds=60,
)
ssrf_guard = SSRFGuard()

# Wire tools
_shell_allowlist = [
    x.strip()
    for x in os.getenv("OM_AI_ALLOWED_SHELL", "echo,pwd,ls").split(",")
    if x.strip()
]
_shell_tool = SafeShellTool(_shell_allowlist)
_kb_tool = KnowledgeSearchTool(knowledge)
_openapi_tool = OpenAPIDiscoveryTool(ssrf_guard=ssrf_guard)

agent = AgentOrchestrator(
    llm_engine=engine,
    knowledge_base=knowledge,
    memory_store=memory,
)
agent.register_tool(_shell_tool)
agent.register_tool(_kb_tool)
agent.register_tool(_openapi_tool)

# OpenAI-compatible shim for OpenClaw / OpenAI SDK clients
from om_ai.api.openai_compat import router as openai_router, bind_engine

_default_model_id = (
    os.getenv("OM_MODEL_ID")
    or os.getenv("OM_AI_MODEL_ID")
    or ("OM-1.0" if configured_backend() == "om_native" else "om-tiny")
)
bind_engine(
    engine,
    default_model_id=_default_model_id,
    native_backend=native_backend,
)
app.include_router(openai_router)

# Optional auto-load of local OM checkpoint (never pulls external LLMs)
_AUTOLOAD = os.getenv("OM_AI_AUTOLOAD", "0") == "1"
_AUTO_CONFIG = os.getenv("OM_AI_CONFIG", "").strip()
_AUTO_TOKENIZER = os.getenv("OM_AI_TOKENIZER", "").strip()
_AUTO_CHECKPOINT = os.getenv("OM_AI_CHECKPOINT", "").strip()
_AUTO_DEVICE = os.getenv("OM_AI_DEVICE")
_NATIVE_MODE = configured_backend() == "om_native"

def _print_native_ready_banner(*, ready: bool, info: dict | None = None) -> None:
    """Print OM native READY banner only after a successful checkpoint load."""
    import sys

    info = info or {}
    tok_info = info.get("tokenizer") or {}
    vocab = tok_info.get("vocab_size") if isinstance(tok_info, dict) else info.get("vocab_size")
    device = info.get("device") or "unknown"
    ckpt_status = "VERIFIED" if ready else "MISSING"
    status = "READY" if ready else "NOT READY — OM-1.0 checkpoint unavailable"
    lines = [
        "====================================",
        "        OM AI NATIVE RUNTIME",
        "====================================",
        "Model:          OM-1.0",
        "Provider:       OM AI",
        "Backend:        OM Native",
        f"Tokenizer:      {vocab if vocab is not None else 'n/a'}",
        f"Checkpoint:     {ckpt_status}",
        f"Device:         {device}",
        "Memory:         ENABLED",
        "Knowledge:      ENABLED",
        "Tools:          ENABLED",
        "External LLM:   NONE",
        "",
        f"Status: {status}",
        "====================================",
    ]
    print("\n".join(lines), file=sys.stderr)


if _NATIVE_MODE:
    # OM native: load only real checkpoint paths; never proxy to third-party LLMs.
    from om_ai.backends.om_registry import sync_om10_registry

    try:
        sync_om10_registry(
            checkpoint=os.getenv("OM_MODEL_CHECKPOINT") or os.getenv("OM_AI_CHECKPOINT") or None,
            tokenizer=os.getenv("OM_MODEL_TOKENIZER") or os.getenv("OM_AI_TOKENIZER") or None,
            config=os.getenv("OM_MODEL_CONFIG") or os.getenv("OM_AI_CONFIG") or None,
            stamp_checkpoint=True,
        )
    except Exception:
        logger.exception("OM-1.0 registry sync failed (non-fatal)")

    paths = default_native_paths()
    try:
        if paths["checkpoint"] and Path(paths["checkpoint"]).is_file():
            info = native_backend.load(
                paths["config"],
                paths["tokenizer"],
                paths["checkpoint"],
                paths["device"] or _AUTO_DEVICE,
                require_checkpoint=True,
            )
            logger.info("OM native autoload succeeded: %s", info)
            agent.llm_engine = engine
            _print_native_ready_banner(ready=True, info=info)
        else:
            logger.error(
                "OM_MODEL_PROVIDER/OM_AI_CHAT_BACKEND=om_native but checkpoint missing — "
                "chat uses the cognitive brain until train-om1 produces a checkpoint. "
                "No Ollama/third-party LLM fallback."
            )
            _print_native_ready_banner(ready=False)
    except Exception as exc:
        logger.exception(
            "OM native autoload failed — %s (chat still uses cognitive brain; no Ollama fallback)",
            exc,
        )
        _print_native_ready_banner(ready=False)
elif _AUTOLOAD:
    try:
        info = engine.load(_AUTO_CONFIG, _AUTO_TOKENIZER, _AUTO_CHECKPOINT, _AUTO_DEVICE)
        logger.info("OM_AI_AUTOLOAD succeeded: %s", info)
        # Keep agent wired to the same engine instance
        agent.llm_engine = engine
        # Reflect loaded local weights on native backend metadata when applicable.
        if _AUTO_CHECKPOINT and Path(_AUTO_CHECKPOINT).is_file():
            native_backend._trained = True
            native_backend._paths = {
                "config": _AUTO_CONFIG,
                "tokenizer": _AUTO_TOKENIZER,
                "checkpoint": _AUTO_CHECKPOINT,
                "device": _AUTO_DEVICE or "",
            }
    except Exception:
        logger.exception("OM_AI_AUTOLOAD failed — API will start without a loaded model")

# Dev-mode warning
if not os.getenv("OM_AI_API_KEYS") and not os.getenv("OM_AI_API_KEYS_FILE") and not os.getenv("OM_AI_API_KEYS_ADMIN"):
    warnings.warn(
        "OM AI is running in OPEN DEV MODE — no API keys configured. "
        "Set OM_AI_API_KEYS, OM_AI_API_KEYS_ADMIN, or OM_AI_API_KEYS_FILE for production use.",
        stacklevel=1,
    )


def _audit(
    action: str,
    actor: str,
    tenant_id: str,
    resource: str = "",
    detail: dict | None = None,
) -> None:
    """Thin wrapper so callers don't repeat keyword noise."""
    try:
        audit_log.record(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            resource=resource,
            detail=detail or {},
        )
    except Exception:
        logger.warning("Audit log write failed for action=%s", action, exc_info=True)


# ---------------------------------------------------------------------------
# Rate-limit middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def _rate_limit_middleware(request: Request, call_next):
    # OM_AI_RATE_LIMIT=0 disables global rate limiting (local dev default).
    if _RATE_LIMIT_MAX <= 0:
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    try:
        rate_limiter.check(client)
    except RateLimitExceeded:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please slow down."},
        )
    return await call_next(request)


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------


class LoadRequest(BaseModel):
    config_path: str
    tokenizer_path: str
    checkpoint_path: str
    device: str | None = None


class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = Field(64, ge=1, le=4096)
    temperature: float = Field(0.8, ge=0.0, le=5.0)
    top_k: int = Field(50, ge=0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(1.0, ge=0.5, le=5.0)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    max_new_tokens: int = Field(256, ge=1, le=4096)
    temperature: float = Field(0.8, ge=0.0, le=5.0)
    top_k: int = Field(50, ge=0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    repetition_penalty: float = Field(1.0, ge=0.5, le=5.0)


class MemoryRequest(BaseModel):
    tenant_id: str = "default"
    user_id: str
    content: str
    kind: str = "conversation"
    metadata: dict = {}


class KnowledgeAddRequest(BaseModel):
    doc_id: str
    text: str
    metadata: dict = {}
    namespace: str = "default"


class KnowledgeIngestRequest(BaseModel):
    source: str = Field(..., description="File path or raw text to ingest")
    doc_id: str | None = None
    namespace: str = "default"
    metadata: dict = {}


class GoalRequest(BaseModel):
    goal: str
    tool_args: dict = {}
    tenant_id: str = "default"


class FeedbackRequest(BaseModel):
    prompt: str
    response: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""
    tenant_id: str = "default"
    user_id: str = "anonymous"


class MultimodalRequest(BaseModel):
    text: str = ""
    image_paths: list[str] = []
    max_new_tokens: int = Field(128, ge=1, le=2048)
    temperature: float = Field(0.8, ge=0.0, le=5.0)


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
def health():
    """Liveness + subsystem snapshot (never 503 — process alive)."""
    model_ready = bool(
        getattr(native_backend, "loaded", False)
        and getattr(native_backend, "_trained", False)
    ) or bool(getattr(engine, "model", None) is not None)
    brain_ok = True
    memory_ok = True
    agents_ok = True
    try:
        from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain  # noqa: F401
    except Exception:
        brain_ok = False
    try:
        memory.all(limit=1) if hasattr(memory, "all") else True
    except Exception:
        try:
            _ = conversations  # noqa: F841
        except Exception:
            memory_ok = False
    try:
        from om_ai.agents.router import AgentRouter

        AgentRouter()
    except Exception:
        agents_ok = False

    status_label = "healthy" if brain_ok else "degraded"
    connectivity: dict = {}
    try:
        from om_ai.runtime.connectivity_bridge import enrich_chat_turn

        snap = enrich_chat_turn("health-ping", intent={"intent": "chat"})
        connectivity = {
            "connected_count": snap.get("connected_count"),
            "connected": snap.get("connected"),
        }
    except Exception as exc:
        connectivity = {"error": str(exc)}
    return {
        "ok": True,
        "status": status_label,
        "brain": brain_ok,
        "memory": memory_ok,
        "model": model_ready,
        "agents": agents_ok,
        "connectivity": connectivity,
        "om_version": "1.0",
        "version": _API_VERSION,
        "foundation": "complete",
        "fallback": None if model_ready else "brain-only",
    }


@app.get("/ready", tags=["System"])
def ready():
    """Readiness probe — 200 only when the model is loaded."""
    loaded = engine.model is not None
    if not loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded yet.",
        )
    return {"ok": True, "model_loaded": True}


# ---------------------------------------------------------------------------
# Model management
# ---------------------------------------------------------------------------


@app.post("/v1/model/load", tags=["Model"])
def load_model(
    req: LoadRequest,
    ctx: TenantContext = Depends(require_permission("model.load")),
):
    """Load (or reload) a local model checkpoint. Admin / operator only."""
    try:
        result = engine.load(
            req.config_path, req.tokenizer_path, req.checkpoint_path, req.device
        )
        _audit(
            "model.load",
            ctx.actor,
            ctx.tenant_id,
            resource="/v1/model/load",
            detail={"checkpoint": req.checkpoint_path},
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/model/info", tags=["Model"])
def model_info(ctx: TenantContext = Depends(require_auth)):
    """Return information about the currently loaded model."""
    if configured_backend() == "om_native":
        return native_backend.model_info()
    return engine.info()


@app.get("/api/v1/model", tags=["Model"])
def api_v1_model(ctx: TenantContext = Depends(require_auth)):
    """Live OM-1.0 / runtime model metadata for UI and clients."""
    from om_ai.runtime.chat_backend import backend_status

    status = backend_status(
        local_loaded=engine.model is not None,
        native_ready=bool(native_backend.loaded and native_backend._trained),
    )
    if configured_backend() == "om_native" or status["backend"] == "om_native":
        from om_ai.backends.om_registry import load_registry_metadata

        info = native_backend.model_info()
        reg = load_registry_metadata() or {}
        return {
            **info,
            "name": info.get("name") or "OM-1.0",
            "provider": "OM AI",
            "backend": "om_native",
            "backend_label": "OM Native",
            "tokenizer_sha256": info.get("tokenizer_fingerprint")
            or reg.get("tokenizer_sha256"),
            "steps": reg.get("steps"),
            "not_70b": True,
            "honesty": reg.get("honesty")
            or "Local OM-1.0 checkpoint; not production frontier intelligence.",
            "chat_status": status,
            "health": native_backend.health(),
            "registry": {
                "checkpoint": reg.get("checkpoint"),
                "lifecycle": reg.get("lifecycle"),
                "trained": reg.get("trained"),
            },
        }
    eng = engine.info()
    return {
        "name": status.get("model") or _default_model_id,
        "provider": status.get("provider") or "OM AI",
        "backend": status.get("backend"),
        "backend_label": status.get("backend"),
        "trained": bool(eng.get("loaded")),
        "loaded": bool(eng.get("loaded")),
        "engine": eng,
        "chat_status": status,
    }


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------


@app.post("/v1/generate", tags=["Generate"])
def generate(
    req: GenerateRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    """Single-shot text generation."""
    try:
        text = engine.generate(
            req.prompt,
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            top_k=req.top_k,
            top_p=req.top_p,
            repetition_penalty=req.repetition_penalty,
        )
        _audit(
            "generate",
            ctx.actor,
            ctx.tenant_id,
            resource="/v1/generate",
            detail={"prompt_len": len(req.prompt)},
        )
        return {"text": text, "model": engine.info().get("checkpoint_path")}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/generate/stream", tags=["Generate"])
async def generate_stream(
    req: GenerateRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    """Server-Sent Events streaming text generation."""

    async def _sse_generator() -> AsyncGenerator[str, None]:
        try:
            for chunk in engine.generate_stream(
                req.prompt,
                max_new_tokens=req.max_new_tokens,
                temperature=req.temperature,
                top_k=req.top_k,
                top_p=req.top_p,
                repetition_penalty=req.repetition_penalty,
            ):
                payload = json.dumps({"token": chunk})
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    _audit(
        "generate.stream",
        ctx.actor,
        ctx.tenant_id,
        resource="/v1/generate/stream",
        detail={"prompt_len": len(req.prompt)},
    )
    return StreamingResponse(_sse_generator(), media_type="text/event-stream")


@app.post("/v1/chat", tags=["Chat"])
def chat(
    req: ChatRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    """Multi-turn chat completion (OM native by default; see OM_AI_CHAT_BACKEND)."""
    from om_ai.runtime.chat_backend import chat_reply

    try:
        messages = [m.model_dump() for m in req.messages]
        reply, backend = chat_reply(
            messages,
            local_chat=engine.chat,
            local_loaded=engine.model is not None,
            native_chat=native_backend.chat,
            native_ready=bool(native_backend.loaded and native_backend._trained),
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            top_k=req.top_k,
            top_p=req.top_p,
            repetition_penalty=req.repetition_penalty,
        )
        _audit(
            "chat",
            ctx.actor,
            ctx.tenant_id,
            resource="/v1/chat",
            detail={"turns": len(messages), "backend": backend.backend},
        )
        payload: dict = {
            "reply": reply,
            "role": "assistant",
            "om_backend": backend.backend,
            "model": backend.model,
            "provider": backend.provider,
        }
        if backend.live_knowledge:
            payload["live_knowledge"] = backend.live_knowledge
        return payload
    except NativeCheckpointError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "OM-1.0 checkpoint unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@app.post("/v1/memory", tags=["Memory"])
def add_memory(
    req: MemoryRequest,
    ctx: TenantContext = Depends(require_permission("memory.write")),
):
    """Store a memory entry for a given tenant / user."""
    record_id = memory.add(
        req.tenant_id, req.user_id, req.content, req.kind, req.metadata
    )
    return {"id": record_id}


@app.get("/v1/memory/{tenant}/{user}", tags=["Memory"])
def get_memory(
    tenant: str,
    user: str,
    limit: int = 20,
    ctx: TenantContext = Depends(require_auth),
):
    """Retrieve recent memory entries for a tenant / user."""
    entries = memory.recent(tenant, user, limit)
    result = []
    for m in entries:
        if hasattr(m, "__dict__"):
            result.append(m.__dict__)
        elif hasattr(m, "__slots__"):
            result.append({s: getattr(m, s) for s in m.__slots__})
        else:
            result.append(m)
    return result


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


@app.post("/v1/knowledge", tags=["Knowledge"])
def add_knowledge(
    req: KnowledgeAddRequest,
    ctx: TenantContext = Depends(require_permission("knowledge.write")),
):
    """Add a document to the knowledge base."""
    try:
        knowledge.add(req.doc_id, req.text, req.metadata, tenant_id=ctx.tenant_id)
        return {"ok": True, "doc_id": req.doc_id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/knowledge/ingest", tags=["Knowledge"])
def ingest_knowledge(
    req: KnowledgeIngestRequest,
    ctx: TenantContext = Depends(require_permission("knowledge.write")),
):
    """Ingest from a file path or raw text string."""
    import os as _os
    import uuid as _uuid

    doc_id = req.doc_id or _uuid.uuid4().hex
    source = req.source

    if len(source) < 4096 and _os.path.isfile(source):
        try:
            text = open(source, encoding="utf-8", errors="replace").read()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot read file: {exc}") from exc
    else:
        text = source

    if not text.strip():
        raise HTTPException(status_code=422, detail="Ingest source is empty.")

    try:
        knowledge.add(doc_id, text, {**req.metadata, "namespace": req.namespace}, tenant_id=ctx.tenant_id)
        _audit(
            "knowledge.ingest",
            ctx.actor,
            ctx.tenant_id,
            resource="/v1/knowledge/ingest",
            detail={"doc_id": doc_id, "chars": len(text)},
        )
        return {"ok": True, "doc_id": doc_id, "chars": len(text)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/knowledge/search", tags=["Knowledge"])
def search_knowledge(
    q: str,
    k: int = 5,
    ctx: TenantContext = Depends(require_auth),
):
    """Full-text / semantic search over the knowledge base."""
    try:
        return knowledge.search_compat(q, k=k, tenant_id=ctx.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


@app.post("/v1/agent/goal", tags=["Agent"])
def run_goal(
    req: GoalRequest,
    ctx: TenantContext = Depends(require_permission("agent.run")),
):
    """Execute an agent goal using the registered tool set."""
    try:
        result = agent.execute_goal(
            req.goal,
            req.tool_args if req.tool_args else None,
            tenant_id=req.tenant_id,
        )
        _audit(
            "agent.goal",
            ctx.actor,
            ctx.tenant_id,
            resource="/v1/agent/goal",
            detail={"goal": req.goal[:200]},
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/v1/agent/tools", tags=["Agent"])
def list_agent_tools(ctx: TenantContext = Depends(require_auth)):
    """Return metadata for all registered agent tools."""
    names = agent.available_tools()
    tools = []
    for name in names:
        entry = agent._tools.get(name)
        if entry:
            tools.append({
                "name": name,
                "risk_level": entry.risk_level,
                "description": entry.description or getattr(entry.tool, "description", ""),
            })
        else:
            tools.append({"name": name})
    return {"tools": tools}


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


@app.post("/v1/feedback", tags=["Feedback"])
def submit_feedback(
    req: FeedbackRequest,
    ctx: TenantContext = Depends(require_permission("feedback.write")),
):
    """Record human feedback on a model response (SQLite; not online weight updates)."""
    fid = feedback_store.add(
        prompt=req.prompt,
        response=req.response,
        rating=req.rating,
        user_id=req.user_id or ctx.actor,
        metadata=json.dumps({"comment": req.comment, "tenant_id": req.tenant_id}),
    )
    _audit(
        "feedback",
        ctx.actor,
        req.tenant_id,
        resource="/v1/feedback",
        detail={
            "rating": req.rating,
            "user_id": req.user_id,
            "comment": req.comment[:500],
            "feedback_id": fid,
        },
    )
    return {
        "ok": True,
        "id": fid,
        "rating": req.rating,
        "database": _FEEDBACK_DB,
        "note": "Saved for later SFT export — does not update model weights online.",
    }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@app.get("/v1/registry", tags=["Registry"])
def list_registry(ctx: TenantContext = Depends(require_auth)):
    """List all registered model versions."""
    return registry.list_versions()


# ---------------------------------------------------------------------------
# API tokens (named) + UI
# ---------------------------------------------------------------------------


class CreateTokenRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    role: str = "operator"
    tenant_id: str = "default"


def _serve_static_html(name: str):
    from fastapi.responses import HTMLResponse
    html_path = Path(__file__).parent / "static" / name
    return HTMLResponse(
        html_path.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


def _serve_tokens_ui():
    return _serve_static_html("tokens.html")


@app.get("/", tags=["UI"])
def ui_home():
    """Entry point: login first. Chat lives at /chat after sign-in."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/login",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/login", tags=["UI"])
def login_page():
    return _serve_static_html("login.html")


@app.get("/register", tags=["UI"])
def register_page():
    return _serve_static_html("register.html")


@app.get("/chat", tags=["UI"])
@app.get("/ui/chat", tags=["UI"])
def chat_ui():
    """Chat console — only useful after account sign-in."""
    return _serve_static_html("chat.html")


@app.get("/ui/tokens", tags=["UI"])
@app.get("/tokens", tags=["UI"])
def tokens_ui():
    """Dedicated API key management page (not the chat UI)."""
    return _serve_tokens_ui()


@app.get("/ui/settings", tags=["UI"])
def settings_ui():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url="/chat#settings",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/v1/tokens/meta", tags=["Tokens"])
def tokens_meta():
    """Public metadata about token database location and model label."""
    from om_ai.security.tokens import get_token_store
    store = get_token_store()
    native = configured_backend() == "om_native"
    model_label = (
        "OM-1.0"
        if native
        else (os.getenv("OM_MODEL_ID") or os.getenv("OM_AI_MODEL_ID", "om:free"))
    )
    return {
        "database": store.path,
        "chat_database": conversations.path,
        "feedback_database": _FEEDBACK_DB,
        "accounts_database": os.getenv("OM_AI_ACCOUNTS_DB", "artifacts/accounts.sqlite3"),
        "model": model_label,
        "provider": "OM AI" if native else None,
        "backend": "om_native" if native else configured_backend(),
        "create_uri": "POST /v1/tokens",
        "list_uri": "GET /v1/tokens",
        "revoke_uri": "DELETE /v1/tokens/{id}",
        "auth_status_uri": "GET /v1/auth/status",
        "register_uri": "POST /v1/auth/register",
        "login_uri": "POST /v1/auth/login",
        "logout_uri": "POST /v1/auth/logout",
        "me_uri": "GET /v1/auth/me",
        "ui": "/chat",
        "login_page": "/login",
        "register_page": "/register",
        "conversations_uri": "/v1/conversations",
    }


@app.post("/v1/tokens", tags=["Tokens"])
def create_token(
    req: CreateTokenRequest,
    ctx: TenantContext = Depends(require_permission("admin.tokens")),
):
    """Create a named API token. Plaintext secret is returned once."""
    from om_ai.security.tokens import get_token_store
    role = (req.role or "agent").strip().lower()
    # Non-admin sessions cannot mint admin tokens.
    if role == "admin" and ctx.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin accounts can create admin API keys.",
        )
    try:
        created = get_token_store().create(
            name=req.name,
            role=role,
            tenant_id=req.tenant_id or ctx.tenant_id,
            owner_actor=ctx.actor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _audit(
        "token.create",
        ctx.actor,
        ctx.tenant_id,
        resource="/v1/tokens",
        detail={"name": req.name, "role": role, "id": created["id"]},
    )
    return created


@app.get("/v1/tokens", tags=["Tokens"])
def list_tokens(
    include_revoked: bool = False,
    ctx: TenantContext = Depends(require_permission("admin.tokens")),
):
    from om_ai.security.tokens import get_token_store
    return {
        "tokens": get_token_store().list(
            include_revoked=include_revoked,
            owner_actor=ctx.actor,
            tenant_id=ctx.tenant_id,
        ),
    }


@app.delete("/v1/tokens/{token_id}", tags=["Tokens"])
def revoke_token(
    token_id: str,
    ctx: TenantContext = Depends(require_permission("admin.tokens")),
):
    from om_ai.security.tokens import get_token_store
    try:
        result = get_token_store().revoke(
            token_id,
            owner_actor=ctx.actor,
            tenant_id=ctx.tenant_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    _audit(
        "token.revoke",
        ctx.actor,
        ctx.tenant_id,
        resource=f"/v1/tokens/{token_id}",
        detail={"id": token_id, "name": result.get("name")},
    )
    return result


# ---------------------------------------------------------------------------
# Multimodal
# ---------------------------------------------------------------------------


@app.post("/v1/multimodal", tags=["Multimodal"])
def multimodal(
    req: MultimodalRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
):
    """Text + optional image / file understanding via multimodal manager."""
    if req.image_paths:
        # Prefer resilient MultimodalManager (OCR + vision reasoning)
        try:
            from om_ai.multimodal.manager import MultimodalManager
            from om_ai.operating_intelligence.universal import UniversalIntelligence

            mm = MultimodalManager()
            path0 = req.image_paths[0]
            packet = mm.process(text=req.text, path=path0, question=req.text)
            uni = UniversalIntelligence().run(
                req.text or "What is in this image?",
                path=path0,
            )
            return {
                "text": uni.get("answer") or packet.get("answer") or "",
                "modalities_used": [packet.get("modality") or "image"],
                "stages": packet.get("stages") or uni.get("stages"),
                "analysis": packet.get("analysis"),
                "ocr": packet.get("ocr"),
            }
        except Exception as exc:
            logger.exception("multimodal manager failed: %s", exc)
            try:
                from om_ai.multimodal.orchestrator import UnifiedOrchestrator
                orch = UnifiedOrchestrator(llm_engine=engine)
                result = orch.run(text=req.text, images=req.image_paths)
                return result
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=(
                        "Vision capability is not available in this deployment. "
                        "Install the vision extras and configure a vision encoder."
                    ),
                )
            except Exception as exc2:
                raise HTTPException(status_code=400, detail=str(exc2)) from exc2
    else:
        try:
            from om_ai.operating_intelligence.universal import UniversalIntelligence

            uni = UniversalIntelligence().run(req.text)
            return {
                "text": uni.get("answer") or "",
                "modalities_used": ["text"],
                "intent": uni.get("intent"),
                "capability": uni.get("capability"),
            }
        except Exception:
            try:
                text = engine.generate(
                    req.text,
                    max_new_tokens=req.max_new_tokens,
                    temperature=req.temperature,
                )
                return {"text": text, "modalities_used": ["text"]}
            except Exception as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/multimodal/analyze", tags=["Multimodal"])
def multimodal_analyze(
    req: MultimodalRequest,
    ctx: TenantContext = Depends(require_auth),
):
    """Lightweight analyze endpoint for chat UI progress display."""
    from om_ai.multimodal.manager import MultimodalManager

    paths = req.image_paths or []
    path0 = paths[0] if paths else None
    packet = MultimodalManager().process(
        text=req.text or "",
        path=path0,
        question=req.text or "",
    )
    return {
        "ok": True,
        "modality": packet.get("modality"),
        "stages": packet.get("stages"),
        "summary": (packet.get("analysis") or {}).get("summary")
        or packet.get("answer")
        or "",
        "ocr": packet.get("ocr"),
        "answer": packet.get("answer"),
    }
