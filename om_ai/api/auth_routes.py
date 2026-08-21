"""Account register / login / logout / me API (cookie + Bearer)."""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from threading import Lock
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth
from om_ai.security.auth import TenantContext
from om_ai.security.session_cookie import (
    clear_session_cookie,
    read_session_cookie,
    set_session_cookie,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])

_AUTH_WINDOW_S = 60.0
_AUTH_MAX_HITS = int(os.getenv("OM_AI_AUTH_RATE_LIMIT", "20"))
_auth_hits: dict[str, list[float]] = defaultdict(list)
_auth_lock = Lock()


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field("", max_length=80)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)


def _store():
    from om_ai.security.accounts import get_account_store

    return get_account_store()


def _register_allowed() -> bool:
    return (os.getenv("OM_AI_ALLOW_REGISTER", "1") or "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_auth_rate(request: Request) -> None:
    ip = _client_ip(request)
    now = time.monotonic()
    with _auth_lock:
        bucket = [t for t in _auth_hits[ip] if now - t < _AUTH_WINDOW_S]
        if len(bucket) >= _AUTH_MAX_HITS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many sign-in attempts. Wait a minute and try again.",
            )
        bucket.append(now)
        _auth_hits[ip] = bucket


def _bearer_or_cookie(request: Request) -> str:
    raw = request.headers.get("X-OM-API-Key") or ""
    auth_header = request.headers.get("Authorization", "")
    if not raw and auth_header.lower().startswith("bearer "):
        raw = auth_header[7:].strip()
    if not raw:
        raw = read_session_cookie(request)
    return raw


def _audit_auth(action: str, actor: str, tenant_id: str, detail: dict | None = None) -> None:
    try:
        from om_ai.api.main import _audit

        _audit(action, actor, tenant_id, resource="/v1/auth", detail=detail or {})
    except Exception:
        logger.debug("auth audit skipped", exc_info=True)


def _sync_chat_profile(user: dict[str, Any]) -> None:
    try:
        from om_ai.api.conversations import get_store

        name = (user.get("display_name") or user.get("email") or "User").strip()
        initial = (name[0] if name else "?").upper()
        actor = f"user:{user['id']}"
        get_store().upsert_profile(
            user.get("tenant_id") or "default",
            actor,
            display_name=name[:80],
            avatar_initial=initial[:2],
        )
    except Exception:
        logger.debug("chat profile sync skipped", exc_info=True)


def _auth_json(result: dict[str, Any]) -> JSONResponse:
    """Return user payload and set HttpOnly session cookie (token not required in JS)."""
    user = result["user"]
    body = {
        "user": user,
        "session_id": result["session_id"],
        "expires_at": result["expires_at"],
        "token_type": "Bearer",
        "cookie_auth": True,
        # Token included for API/CLI clients only — browser UI uses HttpOnly cookie.
        "token": result["token"],
        "note": "Browser session uses a secure HttpOnly cookie. Do not store the token in localStorage.",
    }
    response = JSONResponse(content=body, status_code=200)
    set_session_cookie(response, result["token"], expires_at=result.get("expires_at"))
    return response


@router.get("/v1/auth/status")
def auth_status() -> dict[str, Any]:
    from om_ai.security.accounts import get_account_store

    store = get_account_store()
    return {
        "accounts": True,
        "database": store.path,
        "cookie_auth": True,
        "register_enabled": _register_allowed(),
        "register_uri": "POST /v1/auth/register",
        "login_uri": "POST /v1/auth/login",
        "logout_uri": "POST /v1/auth/logout",
        "me_uri": "GET /v1/auth/me",
        "login_page": "/login",
        "register_page": "/register",
    }


@router.post("/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, request: Request) -> JSONResponse:
    if not _register_allowed():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account registration is disabled on this server.",
        )
    _check_auth_rate(request)
    try:
        result = _store().register(
            email=req.email,
            password=req.password,
            display_name=req.display_name,
            role="agent",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = result["user"]
    _sync_chat_profile(user)
    _audit_auth(
        "auth.register",
        f"user:{user['id']}",
        user.get("tenant_id") or "default",
        {"email": user["email"], "role": user["role"]},
    )
    response = _auth_json(result)
    response.status_code = 201
    return response


@router.post("/v1/auth/login")
def login(req: LoginRequest, request: Request) -> JSONResponse:
    _check_auth_rate(request)
    try:
        result = _store().login(email=req.email, password=req.password)
    except ValueError as exc:
        _audit_auth(
            "auth.login_failed",
            f"email:{(req.email or '')[:64]}",
            "default",
            {"ip": _client_ip(request)},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user = result["user"]
    _sync_chat_profile(user)
    _audit_auth(
        "auth.login",
        f"user:{user['id']}",
        user.get("tenant_id") or "default",
        {"email": user["email"]},
    )
    return _auth_json(result)


@router.post("/v1/auth/logout")
def logout(
    request: Request,
    ctx: TenantContext = Depends(require_auth),
) -> JSONResponse:
    token = _bearer_or_cookie(request)
    result = _store().logout(token)
    _audit_auth(
        "auth.logout",
        ctx.actor,
        ctx.tenant_id,
        {"revoked": bool(result.get("revoked"))},
    )
    body = {"revoked": bool(result.get("revoked")), "actor": ctx.actor}
    response = JSONResponse(content=body)
    clear_session_cookie(response)
    return response


@router.post("/v1/auth/logout-all")
def logout_all(
    request: Request,
    ctx: TenantContext = Depends(require_auth),
) -> JSONResponse:
    if not ctx.actor.startswith("user:"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sign in with an account session to revoke all sessions.",
        )
    user_id = ctx.actor.split(":", 1)[1]
    result = _store().logout_all(user_id)
    _audit_auth("auth.logout_all", ctx.actor, ctx.tenant_id, result)
    response = JSONResponse(content=result)
    clear_session_cookie(response)
    return response


@router.get("/v1/auth/me")
def me(ctx: TenantContext = Depends(require_auth)) -> dict[str, Any]:
    user = None
    last_conversation_id = None
    if ctx.actor.startswith("user:"):
        user_id = ctx.actor.split(":", 1)[1]
        user = _store().get_user(user_id)
        try:
            from om_ai.api.conversations import get_store

            profile = get_store().get_profile(ctx.tenant_id, ctx.actor)
            last_conversation_id = getattr(profile, "last_conversation_id", None) or None
        except Exception:
            last_conversation_id = None
    return {
        "authenticated": True,
        "actor": ctx.actor,
        "role": ctx.role,
        "tenant_id": ctx.tenant_id,
        "user": user,
        "account": user is not None,
        "last_conversation_id": last_conversation_id,
        "cookie_auth": True,
    }
