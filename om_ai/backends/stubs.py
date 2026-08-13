"""Stubs for later OM-1.0 phases (11–15). Not wired into chat this run."""
from __future__ import annotations

from typing import Any, Protocol


class LiveKnowledgeBackend(Protocol):
    """PHASE 11 — TODO: live knowledge / retrieval interface."""

    def retrieve(self, query: str, *, k: int = 5) -> list[dict[str, Any]]: ...


class ToolRouter(Protocol):
    """PHASE 12 — TODO: tool calling router."""

    def list_tools(self) -> list[str]: ...

    def call(self, name: str, arguments: dict[str, Any]) -> Any: ...


class MCPBridge(Protocol):
    """PHASE 13 — TODO: MCP server bridge."""

    def connect(self, endpoint: str) -> None: ...


# PHASE 14–15: RAG orchestration + continuous learning hooks — TODO.
