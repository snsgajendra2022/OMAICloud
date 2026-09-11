"""Platform APIs: workspaces, search, files, library, prompts, tasks, memory, settings, explore."""
from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth
from om_ai.api.platform_store import get_platform_store
from om_ai.api.workspace_store import get_workspace_store
from om_ai.security.auth import TenantContext

router = APIRouter(tags=["Platform"])


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class FileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=240)
    content: str = Field("", max_length=2_000_000)
    mime: str = Field("text/plain", max_length=120)
    content_base64: str | None = None
    project_id: str | None = None


class FileRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=240)


class LibraryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field("", max_length=500_000)
    kind: str = Field("document", max_length=40)
    source_ref: str = Field("", max_length=500)


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=16000)
    kind: str = Field("user", max_length=40)


class PromptUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    content: str | None = Field(None, max_length=16000)
    kind: str | None = Field(None, max_length=40)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    status: str | None = Field(None, max_length=40)
    result: str | None = Field(None, max_length=100_000)


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    importance: float = Field(0.5, ge=0, le=1)
    kind: str = Field("semantic", max_length=40)


class MemoryUpdate(BaseModel):
    content: str | None = Field(None, max_length=4000)
    enabled: bool | None = None
    importance: float | None = Field(None, ge=0, le=1)


class KnowledgeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field("document", max_length=40)
    uri: str = Field("", max_length=1000)
    content: str = Field("", max_length=2_000_000)
    project_id: str | None = None


class SettingsPatch(BaseModel):
    appearance: str | None = None
    default_model: str | None = None
    response_style: str | None = None
    language: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    llm_enabled: bool | None = None
    llm_only: bool | None = None
    memory_enabled: bool | None = None
    rag_enabled: bool | None = None
    live_knowledge_enabled: bool | None = None
    agent_brain_enabled: bool | None = None
    llm_providers: dict[str, bool] | None = None
    llm_api_keys: dict[str, str] | None = None
    notifications_email: bool | None = None
    notifications_push: bool | None = None
    notifications_tasks: bool | None = None
    privacy_history: bool | None = None
    data_collection: bool | None = None


class AssistantUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    system_prompt: str | None = Field(None, max_length=8000)
    model: str | None = Field(None, max_length=64)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    instructions: str | None = Field(None, max_length=8000)


# ---------- Workspaces ----------
@router.get("/v1/workspaces")
def list_workspaces(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    items = get_platform_store().list_workspaces(ctx.tenant_id, ctx.actor)
    return {"workspaces": items}


@router.post("/v1/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    req: WorkspaceCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    return get_platform_store().create_workspace(ctx.tenant_id, ctx.actor, name=req.name)


@router.post("/v1/workspace/bootstrap")
def bootstrap_workspace(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    """Ensure Library / Assistants / Prompts / Memory / welcome chat defaults exist."""
    from om_ai.api.onboarding import bootstrap_user_workspace

    display = ""
    try:
        from om_ai.api.conversations import get_store

        prof = get_store().get_profile(ctx.tenant_id, ctx.actor)
        display = str(getattr(prof, "display_name", "") or "")
    except Exception:
        display = ""
    return bootstrap_user_workspace(ctx.tenant_id, ctx.actor, display_name=display)


# ---------- Search ----------
@router.get("/v1/search")
def global_search(
    q: str = "",
    type: str = "",
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    store = get_platform_store()
    results = store.search_all(ctx.tenant_id, ctx.actor, q, type_filter=type)
    # Include conversations via conversation store when available
    try:
        from om_ai.api.conversations import get_bound_conversation_store

        cstore = get_bound_conversation_store()
        if cstore is not None and q.strip() and (not type or type.lower() in {"", "conversations", "chats"}):
            ql = q.lower()
            # Prefer SQL (title + message body) when the store exposes a connection.
            matched: list[dict[str, Any]] = []
            conn = getattr(cstore, "_conn", None)
            if conn is not None:
                like = f"%{q}%"
                rows = conn.execute(
                    """
                    SELECT c.id, c.title, c.updated_at, c.created_at, c.project_id,
                           (
                             SELECT m.content FROM chat_messages m
                             WHERE m.conversation_id = c.id
                               AND (m.content LIKE ? OR c.title LIKE ?)
                             ORDER BY m.created_at DESC LIMIT 1
                           ) AS snippet
                    FROM conversations c
                    WHERE c.tenant_id = ? AND c.actor = ?
                      AND COALESCE(c.archived, 0) = 0
                      AND (
                        c.title LIKE ?
                        OR EXISTS (
                          SELECT 1 FROM chat_messages m
                          WHERE m.conversation_id = c.id AND m.content LIKE ?
                        )
                      )
                    ORDER BY c.updated_at DESC
                    LIMIT 20
                    """,
                    (like, like, ctx.tenant_id, ctx.actor, like, like),
                ).fetchall()
                for r in rows:
                    item = dict(r)
                    snip = str(item.pop("snippet", None) or "").strip()
                    if snip and ql not in str(item.get("title") or "").lower():
                        item["description"] = snip[:180]
                    matched.append(item)
            else:
                convs = cstore.list_conversations(ctx.tenant_id, actor=ctx.actor)
                for c in convs:
                    item = c.to_dict() if hasattr(c, "to_dict") else dict(c)
                    if ql in str(item.get("title") or "").lower():
                        matched.append(item)
                    if len(matched) >= 20:
                        break
            results["conversations"] = matched
        else:
            results.setdefault("conversations", [])
    except Exception:
        results.setdefault("conversations", [])
    # Projects / assistants
    try:
        ws = get_workspace_store()
        if not type or type.lower() == "projects":
            ql = q.lower()
            results["projects"] = [
                p
                for p in ws.list_projects(ctx.tenant_id, ctx.actor)
                if ql in (p.get("name") or "").lower()
                or ql in (p.get("description") or "").lower()
            ][:20]
        if not type or type.lower() == "assistants":
            ql = q.lower()
            results["assistants"] = [
                a
                for a in ws.list_assistants(ctx.tenant_id, ctx.actor)
                if ql in (a.get("name") or "").lower()
                or ql in (a.get("description") or "").lower()
            ][:20]
    except Exception:
        pass
    return {"query": q, "results": results}


# ---------- Files ----------
@router.get("/v1/files")
def list_files(
    q: str = "",
    project_id: str | None = None,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    return {
        "files": get_platform_store().list_files(
            ctx.tenant_id, ctx.actor, q=q, project_id=project_id or None
        )
    }


@router.post("/v1/files", status_code=status.HTTP_201_CREATED)
def create_file(req: FileCreate, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    raw = None
    if req.content_base64:
        try:
            raw = base64.b64decode(req.content_base64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid content_base64") from exc
    item = get_platform_store().create_file(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        content_text=req.content,
        mime=req.mime,
        raw_bytes=raw,
        project_id=req.project_id,
    )
    get_platform_store().create_notification(
        ctx.tenant_id,
        ctx.actor,
        title="File uploaded",
        body=f"{req.name} is ready in Files.",
    )
    return item


@router.get("/v1/files/{file_id}")
def get_file(file_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        return get_platform_store().get_file(file_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/v1/files/{file_id}")
def rename_file(
    file_id: str, req: FileRename, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().update_file(
            file_id, ctx.tenant_id, ctx.actor, name=req.name
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/v1/files/{file_id}")
def delete_file(file_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        get_platform_store().delete_file(file_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": file_id}


# ---------- Library ----------
@router.get("/v1/library")
def list_library(
    q: str = "",
    kind: str = "",
    favorite: int | None = None,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    items = get_platform_store().list_library(ctx.tenant_id, ctx.actor, q=q)
    if kind.strip():
        k = kind.strip().lower()
        items = [i for i in items if str(i.get("kind") or "").lower() == k]
    if favorite is not None:
        fav = bool(favorite)
        items = [i for i in items if bool(i.get("favorite")) == fav]
    return {"items": items}


@router.post("/v1/library", status_code=status.HTTP_201_CREATED)
def create_library(
    req: LibraryCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    return get_platform_store().create_library_item(
        ctx.tenant_id,
        ctx.actor,
        title=req.title,
        content=req.content,
        kind=req.kind,
        source_ref=req.source_ref,
    )


@router.delete("/v1/library/{item_id}")
def delete_library(item_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        get_platform_store().delete_library_item(item_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": item_id}


# ---------- Prompts ----------
@router.get("/v1/prompts")
def list_prompts(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"prompts": get_platform_store().list_prompts(ctx.tenant_id, ctx.actor)}


@router.post("/v1/prompts", status_code=status.HTTP_201_CREATED)
def create_prompt(req: PromptCreate, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return get_platform_store().create_prompt(
        ctx.tenant_id, ctx.actor, name=req.name, content=req.content, kind=req.kind
    )


@router.patch("/v1/prompts/{prompt_id}")
def update_prompt(
    prompt_id: str, req: PromptUpdate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().update_prompt(
            prompt_id,
            ctx.tenant_id,
            ctx.actor,
            name=req.name,
            content=req.content,
            kind=req.kind,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/v1/prompts/{prompt_id}")
def delete_prompt(prompt_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        get_platform_store().delete_prompt(prompt_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": prompt_id}


# ---------- Tasks ----------
@router.get("/v1/tasks")
def list_tasks(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"tasks": get_platform_store().list_tasks(ctx.tenant_id, ctx.actor)}


@router.post("/v1/tasks", status_code=status.HTTP_201_CREATED)
def create_task(req: TaskCreate, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    task = get_platform_store().create_task(
        ctx.tenant_id, ctx.actor, title=req.title, payload=req.payload, status="running"
    )
    # Complete immediately with a deterministic local result (no fake LLM).
    result = f"Task recorded: {req.title}. Payload keys: {', '.join(sorted(req.payload.keys())) or 'none'}."
    task = get_platform_store().update_task(
        task["id"], ctx.tenant_id, ctx.actor, status="completed", result=result
    )
    get_platform_store().create_notification(
        ctx.tenant_id, ctx.actor, title="Task completed", body=req.title
    )
    return task


@router.patch("/v1/tasks/{task_id}")
def update_task(
    task_id: str, req: TaskUpdate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().update_task(
            task_id, ctx.tenant_id, ctx.actor, status=req.status, result=req.result
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/v1/tasks/{task_id}")
def delete_task(task_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        get_platform_store().delete_task(task_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": task_id}


# ---------- Notifications ----------
@router.get("/v1/notifications")
def list_notifications(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    items = get_platform_store().list_notifications(ctx.tenant_id, ctx.actor)
    unread = sum(1 for n in items if not n.get("read"))
    return {"notifications": items, "unread": unread}


@router.post("/v1/notifications/{notif_id}/read")
def read_notification(
    notif_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().mark_notification_read(
            notif_id, ctx.tenant_id, ctx.actor
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------- Settings ----------
@router.get("/v1/settings")
def get_settings(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"settings": get_platform_store().get_settings_public(ctx.tenant_id, ctx.actor)}


@router.patch("/v1/settings")
def patch_settings(
    req: SettingsPatch, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    patch = req.model_dump(exclude_unset=True)
    return {
        "settings": get_platform_store().update_settings(ctx.tenant_id, ctx.actor, patch)
    }


# ---------- Knowledge ----------
@router.get("/v1/knowledge/sources")
def list_knowledge_sources(
    project_id: str | None = None,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    return {
        "sources": get_platform_store().list_knowledge_sources(
            ctx.tenant_id, ctx.actor, project_id=project_id or None
        )
    }


@router.post("/v1/knowledge/sources", status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    req: KnowledgeCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    store = get_platform_store()
    doc_count = 0
    status_name = "ready"
    # Ingest text into shared KB when content provided
    if req.content.strip():
        try:
            from om_ai.api import main as app_main
            import uuid as _uuid

            doc_id = _uuid.uuid4().hex
            app_main.knowledge.add(
                doc_id,
                req.content,
                {"source": req.name, "actor": ctx.actor, "uri": req.uri},
                tenant_id=ctx.tenant_id,
            )
            doc_count = 1
            status_name = "indexed"
        except Exception:
            store.create_file(
                ctx.tenant_id,
                ctx.actor,
                name=f"{req.name}.txt",
                content_text=req.content,
                mime="text/plain",
            )
            doc_count = 1
            status_name = "stored"
    source = store.create_knowledge_source(
        ctx.tenant_id,
        ctx.actor,
        name=req.name,
        source_type=req.source_type,
        uri=req.uri,
        doc_count=doc_count,
        status=status_name,
        project_id=req.project_id,
    )
    store.create_notification(
        ctx.tenant_id,
        ctx.actor,
        title="Knowledge source added",
        body=req.name,
    )
    return source


@router.delete("/v1/knowledge/sources/{source_id}")
def delete_knowledge_source(
    source_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        get_platform_store().delete_knowledge_source(source_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": source_id}


# ---------- Explore ----------
@router.get("/v1/explore")
def explore(category: str | None = None, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"items": get_platform_store().list_explore(category=category)}


@router.post("/v1/explore/{item_id}/use", status_code=status.HTTP_201_CREATED)
def use_explore_item(item_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    items = get_platform_store().list_explore()
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="explore item not found")
    import json

    try:
        payload = json.loads(item.get("payload") or "{}")
    except json.JSONDecodeError:
        payload = {}
    created: dict[str, Any] = {"explore": item}
    if item["category"] in {"featured", "community"} and payload.get("system_prompt"):
        created["assistant"] = get_workspace_store().create_assistant(
            ctx.tenant_id,
            ctx.actor,
            name=item["title"],
            description=item.get("description") or "",
            system_prompt=str(payload.get("system_prompt") or ""),
            model=str(payload.get("model") or "OM-1.0"),
        )
    elif item["category"] == "template" and payload.get("prompt"):
        created["prompt"] = get_platform_store().create_prompt(
            ctx.tenant_id,
            ctx.actor,
            name=item["title"],
            content=str(payload["prompt"]),
            kind="template",
        )
    else:
        created["task"] = get_platform_store().create_task(
            ctx.tenant_id,
            ctx.actor,
            title=f"Explore: {item['title']}",
            payload={"explore_id": item_id, **payload},
            status="completed",
        )
    return created


# ---------- Memory ----------
@router.get("/v1/memories")
def list_memories(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"memories": get_platform_store().list_memories(ctx.tenant_id, ctx.actor)}


@router.post("/v1/memories", status_code=status.HTTP_201_CREATED)
def create_memory(req: MemoryCreate, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return get_platform_store().create_memory(
        ctx.tenant_id,
        ctx.actor,
        content=req.content,
        importance=req.importance,
        kind=req.kind,
    )


@router.patch("/v1/memories/{memory_id}")
def update_memory(
    memory_id: str, req: MemoryUpdate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().update_memory(
            memory_id,
            ctx.tenant_id,
            ctx.actor,
            content=req.content,
            enabled=req.enabled,
            importance=req.importance,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/v1/memories/{memory_id}")
def delete_memory(memory_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    try:
        get_platform_store().delete_memory(memory_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": memory_id}


# ---------- Models (catalog + user settings) ----------
@router.get("/v1/models/catalog")
def models_catalog(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    settings = get_platform_store().get_settings(ctx.tenant_id, ctx.actor)
    from om_ai.runtime.evolution_matrix import catalog_models, default_evolution_model

    models = catalog_models(settings=settings)
    # Enabled external connectors (Settings → AI)
    from om_ai.runtime.external_llms import LLM_CATALOG, resolve_api_key

    providers = settings.get("llm_providers") or {}
    keys = settings.get("llm_api_keys") or {}
    for pid, meta in LLM_CATALOG.items():
        if meta.get("owned"):
            continue
        if not providers.get(pid):
            continue
        ready = bool(resolve_api_key(pid, keys))
        models.append(
            {
                "id": pid,
                "name": meta["name"],
                "kind": "external",
                "description": f"{meta['vendor']} — {'ready' if ready else 'needs API key in Settings → AI'}",
                "vendor": meta["vendor"],
                "external": True,
                "has_api_key": ready,
                "temperature": settings.get("temperature", 0.7),
                "context_length": "—",
                "max_tokens": settings.get("max_tokens", 1024),
            }
        )
    default = settings.get("default_model") or default_evolution_model()
    return {"models": models, "default_model": default, "evolution_ready": True}


# ---------- History (activity from notifications + tasks) ----------
@router.get("/v1/history")
def activity_history(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    store = get_platform_store()
    notifs = store.list_notifications(ctx.tenant_id, ctx.actor)
    tasks = store.list_tasks(ctx.tenant_id, ctx.actor)
    events = []
    for n in notifs:
        events.append(
            {
                "id": n["id"],
                "kind": "notification",
                "title": n["title"],
                "body": n.get("body") or "",
                "created_at": n["created_at"],
            }
        )
    for t in tasks:
        events.append(
            {
                "id": t["id"],
                "kind": "task",
                "title": t["title"],
                "body": t.get("status") or "",
                "created_at": t.get("updated_at") or t.get("created_at"),
            }
        )
    events.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    return {"events": events[:100]}


# ---------- Profile ----------
@router.get("/v1/profile/me")
def profile_me(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    settings = get_platform_store().get_settings(ctx.tenant_id, ctx.actor)
    return {
        "actor": ctx.actor,
        "tenant_id": ctx.tenant_id,
        "role": getattr(ctx, "role", None) or getattr(ctx, "roles", None),
        "settings": settings,
    }


# ---------- Tools ----------
@router.get("/v1/tools")
def list_platform_tools(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {"tools": get_platform_store().list_tools(ctx.tenant_id, ctx.actor)}


class ToolPatch(BaseModel):
    enabled: bool | None = None
    installed: bool | None = None
    install: bool | None = None  # UI alias
    config: dict[str, Any] | None = None


@router.patch("/v1/tools/{tool_id}")
def patch_tool(
    tool_id: str, req: ToolPatch, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    installed = req.installed if req.installed is not None else req.install
    try:
        return get_platform_store().set_tool(
            ctx.tenant_id,
            ctx.actor,
            tool_id,
            enabled=req.enabled,
            installed=installed,
            config=req.config,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------- Scheduled tasks ----------
class ScheduledTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    schedule: str = Field("daily", max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get("/v1/scheduled-tasks")
def list_scheduled_tasks(
    status: str | None = None, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    store = get_platform_store()
    items = store.list_tasks_by_status(ctx.tenant_id, ctx.actor, status=status)
    scheduled = [
        t for t in items if (t.get("kind") or "") == "scheduled" or t.get("schedule")
    ]
    if status:
        scheduled = [t for t in scheduled if t.get("status") == status]
    return {"tasks": scheduled}


@router.post("/v1/scheduled-tasks", status_code=status.HTTP_201_CREATED)
def create_scheduled_task(
    req: ScheduledTaskCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    return get_platform_store().create_scheduled_task(
        ctx.tenant_id,
        ctx.actor,
        title=req.title,
        schedule=req.schedule,
        payload=req.payload,
    )


# ---------- Project members ----------
class MemberCreate(BaseModel):
    member_email: str | None = Field(None, min_length=3, max_length=200)
    email: str | None = Field(None, min_length=3, max_length=200)
    role: str = Field("viewer", max_length=40)


@router.get("/v1/projects/{project_id}/members")
def list_members(project_id: str, ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return {
        "members": get_platform_store().list_project_members(
            project_id, ctx.tenant_id, ctx.actor
        )
    }


@router.post("/v1/projects/{project_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: str, req: MemberCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    email = (req.member_email or req.email or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="member_email required")
    try:
        return get_platform_store().add_project_member(
            project_id,
            ctx.tenant_id,
            ctx.actor,
            member_email=email,
            role=req.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/v1/projects/{project_id}/members/{member_id}")
def delete_member(
    project_id: str, member_id: str, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        get_platform_store().delete_project_member(member_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": member_id}


# ---------- Instruction versions ----------
class InstructionVersionCreate(BaseModel):
    owner_type: str = Field(..., max_length=40)
    owner_id: str = Field(..., max_length=64)
    content: str = Field(..., min_length=1, max_length=16000)


@router.get("/v1/instructions/versions")
def list_instruction_versions(
    owner_type: str,
    owner_id: str,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    return {
        "versions": get_platform_store().list_instruction_versions(
            ctx.tenant_id, ctx.actor, owner_type=owner_type, owner_id=owner_id
        )
    }


@router.post("/v1/instructions/versions", status_code=status.HTTP_201_CREATED)
def create_instruction_version(
    req: InstructionVersionCreate, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    return get_platform_store().save_instruction_version(
        ctx.tenant_id,
        ctx.actor,
        owner_type=req.owner_type,
        owner_id=req.owner_id,
        content=req.content,
    )


# ---------- Library favorite ----------
class FavoritePatch(BaseModel):
    favorite: bool = True


@router.patch("/v1/library/{item_id}/favorite")
def favorite_library(
    item_id: str, req: FavoritePatch, ctx: TenantContext = Depends(require_auth)
) -> dict[str, Any]:
    try:
        return get_platform_store().set_library_favorite(
            item_id, ctx.tenant_id, ctx.actor, req.favorite
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------- Billing ----------
@router.get("/v1/billing")
def billing(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    return get_platform_store().billing_snapshot(ctx.tenant_id, ctx.actor)
