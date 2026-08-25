"""Identity / RBAC facade over om_ai.security."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class IdentityService:
    def health(self) -> dict[str, Any]:
        return ServiceHealth("identity-service", detail={"auth": "om_ai.security.auth"}).to_dict()

    def status(self) -> dict[str, Any]:
        features = {
            "authentication": True,
            "authorization": True,
            "rbac": True,
            "api_keys": True,
            "audit": True,
        }
        try:
            from om_ai.security import auth

            features["roles_available"] = sorted(getattr(auth, "VALID_ROLES", []))
        except Exception as exc:
            features["auth_import_error"] = str(exc)
        return ok({"features": features, "backend": "om_ai.security"})
