"""Agent communication bus for STEP 26."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from om_ai.core.agents.agent_communication import AgentCommunication


@dataclass
class AgentMessage:
    sender: str
    receiver: str
    content: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    kind: str = "info"  # info | task | result | collab
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "from": self.sender,
            "to": self.receiver,
            "content": self.content,
            "kind": self.kind,
            "timestamp": self.timestamp,
        }


class RuntimeCommunication:
    """Send/broadcast messages and keep an inbox log."""

    def __init__(self) -> None:
        self._base = AgentCommunication()
        self._log: list[AgentMessage] = []
        self._inbox: dict[str, list[AgentMessage]] = {}

    def send(
        self,
        sender: str,
        receiver: str,
        content: str,
        *,
        kind: str = "info",
    ) -> dict[str, Any]:
        msg = AgentMessage(
            sender=sender, receiver=receiver, content=content, kind=kind
        )
        self._base.send(sender, receiver, content)
        self._log.append(msg)
        self._inbox.setdefault(receiver, []).append(msg)
        return msg.to_dict()

    def broadcast(
        self,
        sender: str,
        receivers: list[str],
        content: str,
        *,
        kind: str = "collab",
    ) -> list[dict[str, Any]]:
        return [
            self.send(sender, r, content, kind=kind) for r in receivers if r
        ]

    def inbox(self, agent: str) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._inbox.get(agent, [])]

    def log(self, limit: int = 50) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._log[-limit:]]
