"""Protocol aliases for OM backends — point at real modules (not unfinished work).

Historically this file held PHASE 11–15 TODOs. Those capabilities now live in:
  - live knowledge → ``om_ai.live_knowledge``
  - tools / agent actions → ``om_ai.actions``, ``om_ai.agents``
  - RAG → ``om_ai.knowledge.rag``
  - continuous learning → ``om_ai.continuous``

MCP bridge remains an optional integration contract until a concrete MCP transport
is configured for a deployment.
"""
from __future__ import annotations

from typing import Any, Protocol


class LiveKnowledgeBackend(Protocol):
    """Contract matching live-knowledge retrieval backends."""

    def retrieve(self, query: str, *, k: int = 5) -> list[dict[str, Any]]: ...


class ToolRouter(Protocol):
    """Contract for listing and invoking registered tools."""

    def list_tools(self) -> list[str]: ...

    def call(self, name: str, arguments: dict[str, Any]) -> Any: ...


class MCPBridge(Protocol):
    """Optional Model Context Protocol transport (deployment-specific)."""

    def connect(self, endpoint: str) -> None: ...


def resolve_live_knowledge():
    """Return the in-repo live-knowledge engine factory when available."""
    from om_ai.live_knowledge.engine import LiveKnowledgeEngine

    return LiveKnowledgeEngine


def resolve_tool_surface():
    """Return primary tool/action exports used by the agent stack."""
    from om_ai.actions import KnowledgeSearchTool, SafeShellTool, Tool, ToolResult

    return {
        "Tool": Tool,
        "ToolResult": ToolResult,
        "SafeShellTool": SafeShellTool,
        "KnowledgeSearchTool": KnowledgeSearchTool,
    }
