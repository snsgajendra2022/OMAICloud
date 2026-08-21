"""Conversation / folder / profile REST API for the OM AI chat UI."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth, require_permission
from om_ai.memory.conversations import ConversationStore
from om_ai.security.auth import TenantContext

router = APIRouter(tags=["Conversations"])

_store: ConversationStore | None = None


def bind_conversation_store(store: ConversationStore) -> None:
    global _store
    _store = store


def get_store() -> ConversationStore:
    if _store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conversation store not initialized.",
        )
    return _store


def get_bound_conversation_store() -> ConversationStore | None:
    return _store


# ── Request models ───────────────────────────────────────────────────────────


class CreateConversationRequest(BaseModel):
    title: str = "New chat"
    folder_id: str | None = None
    project_id: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    folder_id: str | None = None
    clear_folder: bool = False
    pinned: bool | None = None
    archived: bool | None = None
    project_id: str | None = None
    clear_project: bool = False
    enable_share: bool = False
    clear_share: bool = False


class AppendMessagesRequest(BaseModel):
    messages: list[dict[str, str]] = Field(..., min_length=1)
    auto_title: bool = True


class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class RenameFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    avatar_initial: str | None = None
    last_conversation_id: str | None = None
    clear_last_conversation: bool = False


class ConversationFeedbackRequest(BaseModel):
    rating: int = Field(5, ge=1, le=5)
    comment: str = ""


# ── Conversations ────────────────────────────────────────────────────────────


@router.get("/v1/conversations")
def list_conversations(
    folder_id: str | None = None,
    unfiled: bool = False,
    project_id: str | None = None,
    include_archived: bool = False,
    archived_only: bool = False,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    items = store.list_conversations(
        ctx.tenant_id,
        ctx.actor,
        folder_id=folder_id,
        unfiled_only=unfiled,
        project_id=project_id,
        include_archived=include_archived,
        archived_only=archived_only,
    )
    return {
        "conversations": [c.to_dict() for c in items],
        "database": store.path,
    }


@router.post("/v1/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    req: CreateConversationRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        conv = store.create_conversation(
            ctx.tenant_id,
            ctx.actor,
            title=req.title,
            folder_id=req.folder_id,
        )
        if req.project_id:
            conv = store.update_conversation(
                conv.id,
                ctx.tenant_id,
                ctx.actor,
                project_id=req.project_id,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return conv.to_dict()


@router.get("/v1/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        conv = store.get_conversation(conversation_id, ctx.tenant_id, ctx.actor)
        messages = store.list_messages(conversation_id, ctx.tenant_id, ctx.actor)
        store.set_last_conversation(ctx.tenant_id, ctx.actor, conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        **conv.to_dict(),
        "messages": [m.to_dict() for m in messages],
    }


@router.patch("/v1/conversations/{conversation_id}")
def update_conversation(
    conversation_id: str,
    req: UpdateConversationRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    folder_arg: Any = ...
    if req.clear_folder:
        folder_arg = None
    elif req.folder_id is not None:
        folder_arg = req.folder_id
    project_arg: Any = ...
    if req.clear_project:
        project_arg = None
    elif req.project_id is not None:
        project_arg = req.project_id
    try:
        conv = store.update_conversation(
            conversation_id,
            ctx.tenant_id,
            ctx.actor,
            title=req.title,
            folder_id=folder_arg,
            pinned=req.pinned,
            archived=req.archived,
            project_id=project_arg,
            enable_share=req.enable_share,
            clear_share=req.clear_share,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return conv.to_dict()


@router.delete("/v1/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        store.delete_conversation(conversation_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": conversation_id}


@router.get("/v1/conversations/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        md = store.export_conversation_markdown(
            conversation_id, ctx.tenant_id, ctx.actor
        )
        conv = store.get_conversation(conversation_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": conversation_id,
        "title": conv.title,
        "format": "markdown",
        "content": md,
    }


@router.post("/v1/conversations/{conversation_id}/share")
def share_conversation(
    conversation_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        conv = store.update_conversation(
            conversation_id,
            ctx.tenant_id,
            ctx.actor,
            enable_share=True,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    token = conv.share_token
    return {
        "id": conversation_id,
        "share_token": token,
        "share_path": f"/share/{token}" if token else None,
        "share_url": f"/share/{token}" if token else None,
    }


@router.delete("/v1/conversations/{conversation_id}/share")
def unshare_conversation(
    conversation_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        conv = store.update_conversation(
            conversation_id,
            ctx.tenant_id,
            ctx.actor,
            clear_share=True,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": conversation_id, "share_token": conv.share_token}


@router.get("/share/{share_token}")
def public_shared_conversation(share_token: str):
    """Public read-only share view (no auth)."""
    store = get_store()
    conv = store.get_conversation_by_share_token(share_token)
    if not conv:
        raise HTTPException(status_code=404, detail="Share link not found")
    messages = store.list_messages(conv.id, conv.tenant_id, conv.actor)
    return {
        "title": conv.title,
        "created_at": conv.created_at,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ],
    }


@router.post("/v1/conversations/{conversation_id}/messages")
def append_messages(
    conversation_id: str,
    req: AppendMessagesRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        created = store.append_messages(
            conversation_id,
            ctx.tenant_id,
            ctx.actor,
            req.messages,
            auto_title=req.auto_title,
        )
        conv = store.get_conversation(conversation_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "conversation": conv.to_dict(),
        "messages": [m.to_dict() for m in created],
    }


@router.post("/v1/conversations/{conversation_id}/feedback")
def save_conversation_feedback(
    conversation_id: str,
    req: ConversationFeedbackRequest,
    ctx: TenantContext = Depends(require_permission("feedback.write")),
):
    """Export conversation turns into FeedbackStore for later SFT export.

    Does **not** update model weights. Use ``om-ai feedback export`` then train.
    """
    from om_ai.continuous.feedback import FeedbackStore
    import json
    import os

    store = get_store()
    try:
        pairs = store.export_for_feedback(conversation_id, ctx.tenant_id, ctx.actor)
        conv = store.get_conversation(conversation_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not pairs:
        raise HTTPException(
            status_code=400,
            detail="No user/assistant turn pairs to save as feedback.",
        )

    fb_path = os.getenv("OM_AI_FEEDBACK_DB", "artifacts/feedback.sqlite3")
    fb = FeedbackStore(fb_path)
    ids: list[str] = []
    for prompt, response in pairs:
        meta = json.dumps(
            {
                "conversation_id": conversation_id,
                "title": conv.title,
                "comment": req.comment,
                "source": "ui_save_as_feedback",
            }
        )
        ids.append(
            fb.add(
                prompt=prompt,
                response=response,
                rating=req.rating,
                user_id=ctx.actor,
                metadata=meta,
            )
        )
    return {
        "ok": True,
        "saved": len(ids),
        "feedback_ids": ids,
        "database": fb_path,
        "note": (
            "Saved for later SFT export. Chat storage does not train the model. "
            "Run: om-ai feedback export — then a training pipeline."
        ),
    }


# ── Folders ──────────────────────────────────────────────────────────────────


@router.get("/v1/folders")
def list_folders(ctx: TenantContext = Depends(require_auth)):
    store = get_store()
    return {"folders": [f.to_dict() for f in store.list_folders(ctx.tenant_id, ctx.actor)]}


@router.post("/v1/folders", status_code=status.HTTP_201_CREATED)
def create_folder(
    req: CreateFolderRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    folder = store.create_folder(ctx.tenant_id, ctx.actor, req.name)
    return folder.to_dict()


@router.patch("/v1/folders/{folder_id}")
def rename_folder(
    folder_id: str,
    req: RenameFolderRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        folder = store.rename_folder(folder_id, ctx.tenant_id, ctx.actor, req.name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return folder.to_dict()


@router.delete("/v1/folders/{folder_id}")
def delete_folder(
    folder_id: str,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    try:
        store.delete_folder(folder_id, ctx.tenant_id, ctx.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, "id": folder_id}


# ── Profile ──────────────────────────────────────────────────────────────────


@router.get("/v1/profile")
def get_profile(ctx: TenantContext = Depends(require_auth)):
    store = get_store()
    profile = store.get_profile(ctx.tenant_id, ctx.actor)
    return {
        **profile.to_dict(),
        "role": ctx.role,
        "account_actor": ctx.actor.startswith("user:"),
    }


@router.put("/v1/profile")
def update_profile(
    req: ProfileUpdateRequest,
    ctx: TenantContext = Depends(require_auth),
):
    store = get_store()
    kwargs: dict[str, Any] = {
        "display_name": req.display_name,
        "avatar_initial": req.avatar_initial,
    }
    if req.clear_last_conversation:
        kwargs["last_conversation_id"] = None
    elif req.last_conversation_id is not None:
        kwargs["last_conversation_id"] = req.last_conversation_id
    profile = store.upsert_profile(
        ctx.tenant_id,
        ctx.actor,
        **kwargs,
    )
    return {**profile.to_dict(), "role": ctx.role}
