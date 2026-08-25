"""Enterprise facade — orgs, roles, API keys, usage, monitoring (wraps tenancy/security)."""
from __future__ import annotations

from typing import Any


def status() -> dict[str, Any]:
    features = {
        "multi_user": True,
        "organizations": True,
        "roles": True,
        "api_keys": True,
        "usage_tracking": "partial",
        "monitoring": True,
        "logs": True,
    }
    detail: dict[str, Any] = {"features": features}
    try:
        from om_ai.tenancy import TenantDirectory

        detail["tenancy"] = "TenantDirectory available"
        detail["tenant_directory"] = TenantDirectory.__name__
    except Exception as exc:
        detail["tenancy_error"] = str(exc)
    try:
        from om_ai.security import auth  # noqa: F401

        detail["security"] = "auth/RBAC available"
    except Exception as exc:
        detail["security_error"] = str(exc)
    try:
        from om_ai import observability  # noqa: F401

        detail["monitoring"] = "observability package available"
    except Exception as exc:
        detail["monitoring_error"] = str(exc)
    return detail
