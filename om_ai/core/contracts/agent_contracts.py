from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class AgentRequest:
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentResult:
    success: bool
    answer: str = ""
    agent: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AgentRouterProtocol(Protocol):
    def route(
        self,
        request: AgentRequest,
    ) -> AgentResult:
        ...


class AgentExecutorProtocol(Protocol):
    def execute(
        self,
        request: AgentRequest,
    ) -> AgentResult:
        ...