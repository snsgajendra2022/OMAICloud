"""Enterprise security facade — wraps om_ai.security."""
from __future__ import annotations

from typing import Any


def status() -> dict[str, Any]:
    out = {
        "authentication": True,
        "authorization": True,
        "rbac": True,
        "api_keys": True,
        "encryption": "transport_tls_recommended",
        "audit_logs": True,
        "secrets_management": "env + OM_AI_API_KEYS",
        "sandbox_execution": "SafeShellTool allowlist",
        "compliance": "tenant_isolation + audit trail",
        "backend": "om_ai.security",
    }
    try:
        from om_ai.security import auth

        out["roles"] = sorted(auth.VALID_ROLES)
    except Exception as exc:
        out["error"] = str(exc)
    return out
