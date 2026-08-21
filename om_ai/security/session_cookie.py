"""HttpOnly session cookie helpers for account auth."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Response

SESSION_COOKIE = os.getenv("OM_AI_SESSION_COOKIE", "om_session")


def cookie_secure() -> bool:
    return (os.getenv("OM_AI_COOKIE_SECURE", "0") or "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def cookie_max_age_seconds(expires_at: str | None = None) -> int:
    default_days = int(os.getenv("OM_AI_SESSION_DAYS", "30"))
    if not expires_at:
        return max(60, default_days * 86400)
    try:
        exp = datetime.fromisoformat(expires_at)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        secs = int((exp - datetime.now(timezone.utc)).total_seconds())
        return max(60, secs)
    except Exception:
        return max(60, default_days * 86400)


def set_session_cookie(response: Response, token: str, *, expires_at: str | None = None) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        max_age=cookie_max_age_seconds(expires_at),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        samesite="lax",
        secure=cookie_secure(),
    )


def read_session_cookie(request: Any) -> str:
    try:
        return (request.cookies.get(SESSION_COOKIE) or "").strip()
    except Exception:
        return ""
