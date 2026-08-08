"""FastAPI auth dependencies (requires fastapi)."""
from __future__ import annotations

from fastapi import HTTPException, Request, status

from om_ai.security.auth import TenantContext, _resolve_context_from_request


async def require_auth(request: Request) -> TenantContext:
    return _resolve_context_from_request(request)


def require_permission(permission: str):
    async def _dep(request: Request) -> TenantContext:
        ctx = _resolve_context_from_request(request)
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required; your role is '{ctx.role}'.",
            )
        return ctx

    return _dep
