"""OM AI security package."""
from __future__ import annotations

from om_ai.security.ssrf import SSRFError, SSRFGuard
from om_ai.security.audit import AuditEntry, AuditLog
from om_ai.security.auth import (
    APIKeyAuth,
    RBAC,
    TenantContext,
    get_current_tenant,
    require_auth_dep,
    require_permission,
    set_current_tenant,
)
from om_ai.security.rate_limit import RateLimitExceeded, RateLimiter
from om_ai.security.secrets import SecretStore
from .controller import SecurityController
from .policy import SecurityPolicy
from .sandbox import SandboxRunner
from .audit_log import AuditLogger
# Back-compat alias
require_auth = require_auth_dep

__all__ = [
    "APIKeyAuth",
    "require_auth",
    "require_auth_dep",
    "require_permission",
    "RateLimiter",
    "RateLimitExceeded",
    "AuditLog",
    "AuditLogger",
    "AuditEntry",
    "SSRFGuard",
    "SSRFError",
    "RBAC",
    "SecretStore",
    "TenantContext",
    "get_current_tenant",
    "set_current_tenant",
    "SecurityController",
    "SecurityPolicy",
    "SandboxRunner"
]
