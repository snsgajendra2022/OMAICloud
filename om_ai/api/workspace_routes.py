"""Projects & assistants workspace APIs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth
from om_ai.api.workspace_store import get_workspace_store
from om_ai.security.auth import TenantContext

router = APIRouter(tags=["Workspace"])


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=2000)
    instructions: str = Field("", max_length=8000)


class AssistantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field("", max_length=2000)
    system_prompt: str = Field("", max_length=8000)
    model: str = Field("OM-1.0", max_length=64)


@router.get("/v1/projects")
def list_projects(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    items = get_workspace_store().list_projects(ctx.tenant_id, ctx.actor)
    return {"projects": items}


@router.get("/v1/projects/{project_id}")
def get_project(project_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        proj = get_workspace_store().get_project(project_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    # Enrich with light counts from platform/conversations when available
    try:
        from om_ai.api.conversations import get_bound_conversation_store
        from om_ai.api.platform_store import get_platform_store

        cstore = get_bound_conversation_store()
        chats = []
        if cstore is not None:
            chats = cstore.list_conversations(
                ctx.tenant_id, ctx.actor, project_id=project_id
            )
        members = get_platform_store().list_project_members(
            project_id, ctx.tenant_id, ctx.actor
        )
        files = [
            f
            for f in get_platform_store().list_files(ctx.tenant_id, ctx.actor)
            if f.get("project_id") == project_id
        ]
        proj = {
            **proj,
            "chat_count": len(chats),
            "member_count": len(members),
            "file_count": len(files),
        }
    except Exception:
        proj = {**proj, "chat_count": 0, "member_count": 0, "file_count": 0}
    return proj


@router.post("/v1/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    req: ProjectCreate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    return get_workspace_store().create_project(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        description=req.description,
        instructions=req.instructions,
    )


@router.delete("/v1/projects/{project_id}")
def delete_project(
    project_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        get_workspace_store().delete_project(project_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": project_id}


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


class AssistantUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    system_prompt: str | None = Field(None, max_length=8000)
    model: str | None = Field(None, max_length=64)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=8000)


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


@router.patch("/v1/projects/{project_id}")
def update_project(
    project_id: str,
    req: ProjectUpdate,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    try:
        return get_workspace_store().update_project(
            project_id,
            ctx.tenant_id,
            ctx.actor,
            name=req.name,
            description=req.description,
            instructions=req.instructions,
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


@router.post("/v1/system-prompts/{prompt_id}/activate")
def activate_system_prompt(
    prompt_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    from om_ai.runtime.system_prompts import get_system_prompt_store

    try:
        return get_system_prompt_store().set_active(prompt_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
