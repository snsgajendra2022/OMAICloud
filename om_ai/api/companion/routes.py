"""Companion API routes — STEP 50 integration."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companion", tags=["companion"])


class MessageBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    history: list[dict[str, Any]] | None = None
    session_id: str | None = None


class DeviceBody(BaseModel):
    input_device_id: int


class PermissionBody(BaseModel):
    decision: str = Field(..., pattern="^(approve|deny)$")


def _runtime():
    from om_ai.core.companion_runtime import get_companion_runtime

    return get_companion_runtime()


@router.get("/status")
def companion_status() -> dict[str, Any]:
    rt = _runtime()
    if not rt._started:
        # probe without full audio start in API status
        return {"started": False, **rt.status_banner()}
    return {"started": True, **rt.status_banner()}


@router.post("/session")
def companion_session() -> dict[str, Any]:
    rt = _runtime()
    if not rt._started:
        rt.config.text_only = True
        rt.config.wake_word_enabled = False
        banner = rt.start()
    else:
        banner = rt.status_banner()
    return {"session_id": rt.context.session_id, "status": banner}


@router.post("/message")
def companion_message(body: MessageBody) -> dict[str, Any]:
    rt = _runtime()
    if not rt._started:
        rt.config.text_only = True
        rt.start()
    out = rt.handle_text(body.text, history=body.history)
    return out


@router.post("/interrupt")
def companion_interrupt() -> dict[str, Any]:
    return _runtime().interrupt()


@router.post("/mute")
def companion_mute() -> dict[str, Any]:
    rt = _runtime()
    if rt.voice:
        rt.voice.mute()
    return {"ok": True, "muted": True}


@router.post("/unmute")
def companion_unmute() -> dict[str, Any]:
    rt = _runtime()
    if rt.voice:
        rt.voice.unmute()
    return {"ok": True, "muted": False}


@router.get("/devices")
def companion_devices() -> dict[str, Any]:
    from om_ai.core.voice_intelligence import AudioDeviceManager

    return AudioDeviceManager().status()


@router.post("/device")
def companion_select_device(body: DeviceBody) -> dict[str, Any]:
    from om_ai.core.voice_intelligence import AudioDeviceManager

    return AudioDeviceManager().select_input(body.input_device_id)


@router.get("/permissions")
def companion_permissions() -> dict[str, Any]:
    rt = _runtime()
    pending = None
    if rt.voice and rt.voice.session.pending_permission_id:
        pending = {
            "permission_id": rt.voice.session.pending_permission_id,
            "action": rt.voice.session.pending_action,
        }
    return {"pending": pending}


@router.post("/permissions/{permission_id}/approve")
def companion_approve(permission_id: str) -> dict[str, Any]:
    rt = _runtime()
    if not rt.voice or rt.voice.session.pending_permission_id != permission_id:
        raise HTTPException(status_code=404, detail="permission_not_found")
    return rt.handle_text("yes")


@router.post("/permissions/{permission_id}/deny")
def companion_deny(permission_id: str) -> dict[str, Any]:
    rt = _runtime()
    if not rt.voice or rt.voice.session.pending_permission_id != permission_id:
        raise HTTPException(status_code=404, detail="permission_not_found")
    return rt.handle_text("no")


@router.get("/memory")
def companion_memory() -> dict[str, Any]:
    rt = _runtime()
    mem = rt.memory
    if mem is None:
        try:
            from om_ai.core.companion_memory import MemoryService

            mem = MemoryService()
        except Exception as exc:
            return {"error": str(exc)}
    if hasattr(mem, "list_all"):
        return mem.list_all()
    if hasattr(mem, "snapshot"):
        return mem.snapshot()
    return {"memory": str(mem)}


@router.websocket("/ws/{session_id}")
async def companion_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    rt = _runtime()
    if not rt._started:
        rt.config.text_only = True
        rt.start()
    if rt.realtime is not None:
        try:
            rt.realtime.streams.hub.register(session_id, websocket)
        except Exception:
            pass
    try:
        await websocket.send_json(
            {
                "event_type": "companion.state",
                "session_id": session_id,
                "payload": {"state": rt.status_banner().get("status")},
            }
        )
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue
            typ = str(data.get("type") or data.get("event_type") or "")
            if typ in {"message", "user.message"}:
                text = str(data.get("text") or data.get("payload", {}).get("text") or "")
                out = rt.handle_text(text)
                await websocket.send_json(
                    {
                        "event_type": "response.delta",
                        "session_id": session_id,
                        "payload": out,
                    }
                )
            elif typ == "interrupt":
                await websocket.send_json({"event_type": "voice.interrupted", "payload": rt.interrupt()})
            elif typ == "ping":
                await websocket.send_json({"event_type": "pong", "payload": {}})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("companion ws closed: %s", exc)
    finally:
        if rt.realtime is not None:
            try:
                rt.realtime.streams.hub.unregister(session_id, websocket)
            except Exception:
                pass
