"""Projects & assistants workspace APIs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth
from om_ai.api.workspace_store import get_workspace_store
from om_ai.security.auth import TenantContext

router = APIRouter(tags=["Workspace"])


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=2000)
    instructions: str = Field("", max_length=8000)
    model: str = Field("OM-L5", max_length=64)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=8000)
    model: str | None = Field(None, max_length=64)
    favorite: bool | None = None
    archived: bool | None = None


class AssistantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=2000)
    system_prompt: str = Field("", max_length=8000)
    model: str = Field("OM-L5", max_length=64)


class AssistantUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    system_prompt: str | None = Field(None, max_length=8000)
    model: str | None = Field(None, max_length=64)


class ProjectChatCreate(BaseModel):
    title: str = Field("New chat", max_length=200)


class ProjectFileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=240)
    content: str = Field("", max_length=500_000)
    mime: str = Field("text/plain", max_length=120)
    content_base64: str | None = None


class ProjectMemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    importance: float = Field(0.7, ge=0.0, le=1.0)


class ProjectKnowledgeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field("document", max_length=40)
    uri: str = Field("", max_length=1000)


def _enrich_project(proj: dict[str, Any], tenant_id: str, actor: str) -> dict[str, Any]:
    try:
        from om_ai.api.conversations import get_bound_conversation_store
        from om_ai.api.platform_store import get_platform_store

        cstore = get_bound_conversation_store()
        chats = []
        if cstore is not None:
            chats = cstore.list_conversations(
                tenant_id, actor, project_id=proj["id"]
            )
        members = get_platform_store().list_project_members(
            proj["id"], tenant_id, actor
        )
        files = get_platform_store().list_files(
            tenant_id, actor, project_id=proj["id"]
        )
        memories = get_platform_store().list_project_memories(
            proj["id"], tenant_id, actor
        )
        knowledge = get_platform_store().list_knowledge_sources(
            tenant_id, actor, project_id=proj["id"]
        )
        return {
            **proj,
            "chat_count": len(chats),
            "member_count": len(members),
            "file_count": len(files),
            "memory_count": len(memories),
            "knowledge_count": len(knowledge),
        }
    except Exception:
        return {
            **proj,
            "chat_count": 0,
            "member_count": 0,
            "file_count": 0,
            "memory_count": 0,
            "knowledge_count": 0,
        }


def _get_owned_project(project_id: str, ctx: TenantContext) -> dict[str, Any]:
    try:
        return get_workspace_store().get_project(project_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Projects CRUD ────────────────────────────────────────────────────────────


@router.get("/v1/projects")
@router.get("/api/projects")
def list_projects(
    q: str = "",
    sort: str = Query("updated"),
    filter_mode: str = Query("all", alias="filter"),
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    mode = (filter_mode or "all").strip().lower()
    if mode not in {"all", "favorites", "archived", "recent"}:
        mode = "all"
    sort_key = (sort or "updated").strip().lower()
    if sort_key not in {"updated", "name", "created", "favorite"}:
        sort_key = "updated"
    items = get_workspace_store().list_projects(
        ctx.tenant_id,
        ctx.actor,
        q=q,
        sort=sort_key,
        filter_mode=mode,
    )
    enriched = [_enrich_project(p, ctx.tenant_id, ctx.actor) for p in items]
    return {"projects": enriched}


@router.get("/v1/projects/{project_id}")
@router.get("/api/projects/{project_id}")
def get_project(project_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    proj = _get_owned_project(project_id, ctx)
    return _enrich_project(proj, ctx.tenant_id, ctx.actor)


@router.post("/v1/projects", status_code=status.HTTP_201_CREATED)
@router.post("/api/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    req: ProjectCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    proj = get_workspace_store().create_project(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        description=req.description,
        instructions=req.instructions,
        model=req.model,
    )
    if req.instructions.strip():
        try:
            from om_ai.api.platform_store import get_platform_store

            get_platform_store().save_instruction_version(
                ctx.tenant_id,
                ctx.actor,
                owner_type="project",
                owner_id=proj["id"],
                content=req.instructions,
            )
        except Exception:
            pass
    return _enrich_project(proj, ctx.tenant_id, ctx.actor)


@router.patch("/v1/projects/{project_id}")
@router.put("/v1/projects/{project_id}")
@router.patch("/api/projects/{project_id}")
@router.put("/api/projects/{project_id}")
def update_project(
    project_id: str,
    req: ProjectUpdate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        proj = get_workspace_store().update_project(
            project_id,
            ctx.tenant_id,
            ctx.actor,
            name=req.name,
            description=req.description,
            instructions=req.instructions,
            model=req.model,
            favorite=req.favorite,
            archived=req.archived,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if req.instructions is not None and req.instructions.strip():
        try:
            from om_ai.api.platform_store import get_platform_store

            get_platform_store().save_instruction_version(
                ctx.tenant_id,
                ctx.actor,
                owner_type="project",
                owner_id=project_id,
                content=req.instructions,
            )
        except Exception:
            pass
    return _enrich_project(proj, ctx.tenant_id, ctx.actor)


@router.delete("/v1/projects/{project_id}")
@router.delete("/api/projects/{project_id}")
def delete_project(
    project_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        get_workspace_store().delete_project(project_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": project_id}


@router.post(
    "/v1/projects/{project_id}/duplicate", status_code=status.HTTP_201_CREATED
)
@router.post(
    "/api/projects/{project_id}/duplicate", status_code=status.HTTP_201_CREATED
)
def duplicate_project(
    project_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        proj = get_workspace_store().duplicate_project(
            project_id, ctx.tenant_id, ctx.actor
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _enrich_project(proj, ctx.tenant_id, ctx.actor)


# ── Project chats ────────────────────────────────────────────────────────────


@router.get("/v1/projects/{project_id}/chats")
@router.get("/api/projects/{project_id}/chats")
def list_project_chats(
    project_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.conversations import get_bound_conversation_store

    cstore = get_bound_conversation_store()
    if cstore is None:
        return {"chats": [], "conversations": []}
    chats = cstore.list_conversations(
        ctx.tenant_id, ctx.actor, project_id=project_id
    )
    payload = [c.to_dict() for c in chats]
    return {"chats": payload, "conversations": payload}


@router.post(
    "/v1/projects/{project_id}/chats", status_code=status.HTTP_201_CREATED
)
@router.post(
    "/api/projects/{project_id}/chats", status_code=status.HTTP_201_CREATED
)
def create_project_chat(
    project_id: str,
    req: ProjectChatCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.conversations import get_bound_conversation_store

    cstore = get_bound_conversation_store()
    if cstore is None:
        raise HTTPException(status_code=503, detail="Conversation store not ready")
    conv = cstore.create_conversation(
        ctx.tenant_id, ctx.actor, title=req.title or "New chat"
    )
    conv = cstore.update_conversation(
        conv.id, ctx.tenant_id, ctx.actor, project_id=project_id
    )
    return conv.to_dict()


# ── Project files ────────────────────────────────────────────────────────────


@router.get("/v1/projects/{project_id}/files")
@router.get("/api/projects/{project_id}/files")
def list_project_files(
    project_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    return {
        "files": get_platform_store().list_files(
            ctx.tenant_id, ctx.actor, project_id=project_id
        )
    }


@router.post(
    "/v1/projects/{project_id}/files", status_code=status.HTTP_201_CREATED
)
@router.post(
    "/api/projects/{project_id}/files", status_code=status.HTTP_201_CREATED
)
def upload_project_file(
    project_id: str,
    req: ProjectFileCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    import base64

    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    raw = None
    if req.content_base64:
        try:
            raw = base64.b64decode(req.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid content_base64") from exc
    return get_platform_store().create_file(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        content_text=req.content,
        mime=req.mime,
        raw_bytes=raw,
        project_id=project_id,
    )


@router.delete("/v1/projects/{project_id}/files/{file_id}")
@router.delete("/api/projects/{project_id}/files/{file_id}")
def remove_project_file(
    project_id: str,
    file_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    try:
        item = get_platform_store().get_file(file_id, ctx.tenant_id, ctx.actor)
        if item.get("project_id") != project_id:
            raise HTTPException(status_code=404, detail="file not in project")
        get_platform_store().clear_file_project(file_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": file_id}


# ── Project memory ───────────────────────────────────────────────────────────


@router.get("/v1/projects/{project_id}/memory")
@router.get("/api/projects/{project_id}/memory")
def list_project_memory(
    project_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    return {
        "memories": get_platform_store().list_project_memories(
            project_id, ctx.tenant_id, ctx.actor
        )
    }


@router.post(
    "/v1/projects/{project_id}/memory", status_code=status.HTTP_201_CREATED
)
@router.post(
    "/api/projects/{project_id}/memory", status_code=status.HTTP_201_CREATED
)
def create_project_memory(
    project_id: str,
    req: ProjectMemoryCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    return get_platform_store().create_project_memory(
        project_id,
        ctx.tenant_id,
        ctx.actor,
        content=req.content,
        importance=req.importance,
    )


@router.delete("/v1/projects/{project_id}/memory/{memory_id}")
@router.delete("/api/projects/{project_id}/memory/{memory_id}")
def delete_project_memory(
    project_id: str,
    memory_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    try:
        get_platform_store().delete_project_memory(
            memory_id, project_id, ctx.tenant_id, ctx.actor
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": memory_id}


# ── Project knowledge ────────────────────────────────────────────────────────


@router.get("/v1/projects/{project_id}/knowledge")
@router.get("/api/projects/{project_id}/knowledge")
def list_project_knowledge(
    project_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    return {
        "sources": get_platform_store().list_knowledge_sources(
            ctx.tenant_id, ctx.actor, project_id=project_id
        )
    }


@router.post(
    "/v1/projects/{project_id}/knowledge", status_code=status.HTTP_201_CREATED
)
@router.post(
    "/api/projects/{project_id}/knowledge", status_code=status.HTTP_201_CREATED
)
def create_project_knowledge(
    project_id: str,
    req: ProjectKnowledgeCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    _get_owned_project(project_id, ctx)
    from om_ai.api.platform_store import get_platform_store

    return get_platform_store().create_knowledge_source(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        source_type=req.source_type,
        uri=req.uri,
        project_id=project_id,
        status="ready",
    )


# ── Assistants ───────────────────────────────────────────────────────────────


@router.get("/v1/assistants")
def list_assistants(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    items = get_workspace_store().list_assistants(ctx.tenant_id, ctx.actor)
    return {"assistants": items}


@router.post("/v1/assistants", status_code=status.HTTP_201_CREATED)
def create_assistant(
    req: AssistantCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    return get_workspace_store().create_assistant(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        description=req.description,
        system_prompt=req.system_prompt,
        model=req.model,
    )


@router.delete("/v1/assistants/{assistant_id}")
def delete_assistant(
    assistant_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        get_workspace_store().delete_assistant(assistant_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": assistant_id}


@router.patch("/v1/assistants/{assistant_id}")
def update_assistant(
    assistant_id: str,
    req: AssistantUpdate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        return get_workspace_store().update_assistant(
            assistant_id,
            ctx.tenant_id,
            ctx.actor,
            name=req.name,
            description=req.description,
            system_prompt=req.system_prompt,
            model=req.model,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/v1/assistants/{assistant_id}/duplicate", status_code=status.HTTP_201_CREATED)
def duplicate_assistant(
    assistant_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        return get_workspace_store().duplicate_assistant(
            assistant_id, ctx.tenant_id, ctx.actor
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class SystemPromptUpsert(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=16000)
    active: bool = False


@router.get("/v1/system-prompts")
def list_system_prompts(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    from om_ai.runtime.system_prompts import get_system_prompt_store

    store = get_system_prompt_store()
    return {"prompts": store.list_prompts(), "active": store.get_active()}


@router.post("/v1/system-prompts", status_code=status.HTTP_201_CREATED)
def upsert_system_prompt(
    req: SystemPromptUpsert,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    from om_ai.runtime.system_prompts import get_system_prompt_store

    try:
        return get_system_prompt_store().upsert(
            name=req.name, content=req.content, active=req.active
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/v1/system-prompts/{name}")
def delete_system_prompt(
    name: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    from om_ai.runtime.system_prompts import get_system_prompt_store

    try:
        get_system_prompt_store().delete(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "name": name}
