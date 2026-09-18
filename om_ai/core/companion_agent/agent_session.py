"""Session state for a companion agent run."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from om_ai.core.companion_security import SecurityContext

from .cancellation_manager import CancellationToken
from .goal import Goal
from .task_graph import TaskGraph


@dataclass
class AgentSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    security: SecurityContext | None = None
    goals: list[Goal] = field(default_factory=list)
    graph: TaskGraph = field(default_factory=TaskGraph)
    cancel_token: CancellationToken | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def context(self) -> SecurityContext:
        if self.security is None:
            self.security = SecurityContext(session_id=self.session_id)
        return self.security
