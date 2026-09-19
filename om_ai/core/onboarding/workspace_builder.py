"""Production workspace creator — personalized OM environment shell."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class WorkspaceBuilder:
    def create(
        self,
        tenant_id: str,
        actor: str,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        name = f"{profile.get('display_name', 'User')}'s OM"
        workspace = {
            "tenant_id": tenant_id,
            "user_id": actor,
            "name": name,
            "mode": profile.get("purpose", "general"),
            "language": profile.get("language", "auto"),
            "companion_enabled": True,
            "memory_enabled": True,
            "created": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("OM workspace created user=%s name=%s", actor, name)
        return workspace
