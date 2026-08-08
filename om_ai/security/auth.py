"""Authentication, authorisation, RBAC and tenant context for OM AI."""
from __future__ import annotations

import json
import logging
import os
import uuid
import warnings
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset({
        "model.load", "model.generate", "agent.run", "memory.write",
        "knowledge.write", "admin.registry", "admin.tokens", "feedback.write",
        "tool.shell", "tool.openapi",
    }),
    "operator": frozenset({
        "model.load", "model.generate", "agent.run", "memory.write",
        "knowledge.write", "feedback.write", "tool.openapi",
    }),
    "agent": frozenset({
        "model.generate", "agent.run", "memory.write",
        "knowledge.write", "feedback.write", "tool.openapi",
    }),
    "viewer": frozenset({"model.generate"}),
}

VALID_ROLES: frozenset[str] = frozenset(_ROLE_PERMISSIONS)


class RBAC:
    def can(self, role: str, permission: str) -> bool:
        return permission in _ROLE_PERMISSIONS.get(role, frozenset())

    def require(self, role: str, permission: str) -> None:
        if not self.can(role, permission):
            raise PermissionError(f"Role '{role}' does not have permission '{permission}'")

    def permissions_for(self, role: str) -> frozenset[str]:
        return _ROLE_PERMISSIONS.get(role, frozenset())


rbac = RBAC()


@dataclass
class TenantContext:
    tenant_id: str = "default"
    actor: str = "anonymous"
    role: str = "viewer"
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def has_permission(self, permission: str) -> bool:
        return rbac.can(self.role, permission)


_current_tenant: ContextVar[TenantContext] = ContextVar(
    "_current_tenant", default=TenantContext()
)


def get_current_tenant() -> TenantContext:
    return _current_tenant.get()


def set_current_tenant(ctx: TenantContext) -> None:
    _current_tenant.set(ctx)


def _load_api_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    keys_env = os.getenv("OM_AI_API_KEYS", "").strip()
    if keys_env:
        for raw in keys_env.split(","):
            raw = raw.strip()
            if ":" in raw:
                k, _, role = raw.partition(":")
                role = role.strip() if role.strip() in VALID_ROLES else "viewer"
                keys[k.strip()] = role
            elif raw:
                keys[raw] = "operator"
    keys_file = os.getenv("OM_AI_API_KEYS_FILE", "").strip()
    if keys_file and os.path.isfile(keys_file):
        with open(keys_file) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            for k, role in data.items():
                keys[str(k)] = role if role in VALID_ROLES else "viewer"
    return keys


class APIKeyAuth:
    def __init__(self) -> None:
        self._keys: dict[str, str] = {}
        self._dev_mode: bool = False
        self.reload()

    def reload(self) -> None:
        self._keys = _load_api_keys()
        if not self._keys:
            # DB tokens alone are enough — don't force open/dev mode if tokens DB may have keys
            try:
                from om_ai.security.tokens import get_token_store
                if get_token_store().list():
                    self._dev_mode = False
                    return
            except Exception:
                pass
            if os.getenv("OM_AI_REQUIRE_AUTH", "0") == "1":
                warnings.warn(
                    "OM_AI_REQUIRE_AUTH=1 but no keys configured – all requests will be rejected.",
                    stacklevel=2,
                )
                self._dev_mode = False
            else:
                warnings.warn(
                    "No API keys configured – running in dev mode. "
                    "Set OM_AI_API_KEYS or create a token via POST /v1/tokens.",
                    stacklevel=2,
                )
                self._dev_mode = True
        else:
            self._dev_mode = False

    def validate(self, key: str) -> Optional[str]:
        """Return role for env key, or None. DB tokens validated separately."""
        return self._keys.get(key)

    def validate_full(self, key: str) -> Optional[dict]:
        """Validate env or DB token. Returns {role, name, tenant_id, source}."""
        role = self._keys.get(key)
        if role:
            return {"role": role, "name": "env-key", "tenant_id": "default", "source": "env"}
        try:
            from om_ai.security.tokens import get_token_store
            rec = get_token_store().validate(key)
            if rec:
                return {
                    "role": rec["role"],
                    "name": rec["name"],
                    "tenant_id": rec["tenant_id"],
                    "source": "db",
                    "id": rec["id"],
                }
        except Exception:
            logger.exception("token DB validate failed")
        return None

    def is_dev_mode(self) -> bool:
        return self._dev_mode

    @property
    def key_count(self) -> int:
        return len(self._keys)


_auth_instance: Optional[APIKeyAuth] = None


def _get_auth() -> APIKeyAuth:
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = APIKeyAuth()
    return _auth_instance


def _resolve_context_from_request(request) -> TenantContext:
    from fastapi import HTTPException, status

    auth = _get_auth()
    require_strict = os.getenv("OM_AI_REQUIRE_AUTH", "0") == "1"
    request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex)
    client_host = request.client.host if request.client else "unknown"
    is_local = client_host in ("127.0.0.1", "::1", "localhost")

    if auth.is_dev_mode() and not require_strict:
        ctx = TenantContext(
            tenant_id=request.headers.get("X-Tenant-Id", "default"),
            actor=f"dev:{client_host}",
            role="admin" if is_local else "viewer",
            request_id=request_id,
        )
        set_current_tenant(ctx)
        return ctx

    raw_key = request.headers.get("X-OM-API-Key") or ""
    auth_header = request.headers.get("Authorization", "")
    if not raw_key and auth_header.lower().startswith("bearer "):
        raw_key = auth_header[7:].strip()
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-OM-API-Key or Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    info = auth.validate_full(raw_key)
    if info is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key.")
    ctx = TenantContext(
        tenant_id=request.headers.get("X-Tenant-Id", info.get("tenant_id", "default")),
        actor=f"{info.get('source', 'key')}:{info.get('name', raw_key[:6])}…",
        role=info["role"],
        request_id=request_id,
    )
    set_current_tenant(ctx)
    return ctx


async def require_auth(request=None):
    """FastAPI dependency: Depends(require_auth)."""
    from fastapi import Request

    if not isinstance(request, Request):
        raise RuntimeError("require_auth must be used as a FastAPI dependency")
    return _resolve_context_from_request(request)


# Alias used by some callers
require_auth_dep = require_auth


def require_permission(permission: str):
    """FastAPI dependency factory: Depends(require_permission('model.generate'))."""

    async def _dep(request=None):
        from fastapi import HTTPException, Request, status

        if not isinstance(request, Request):
            raise RuntimeError("require_permission must be used as a FastAPI dependency")
        ctx = _resolve_context_from_request(request)
        if not ctx.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required; your role is '{ctx.role}'.",
            )
        return ctx

    return _dep
