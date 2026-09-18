"""Security context for companion operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SecurityContext:
    session_id: str
    actor: str = "operator"
    trust_boundary: str = "internal"
    content_origin: str = "internal"
    roles: tuple[str, ...] = ("user",)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_external_content(self) -> bool:
        return self.content_origin == "external" or self.trust_boundary == "external"

    def with_internal_actor(self) -> SecurityContext:
        return SecurityContext(
            session_id=self.session_id,
            actor=self.actor,
            trust_boundary="internal",
            content_origin="internal",
            roles=self.roles,
            metadata=dict(self.metadata),
        )
