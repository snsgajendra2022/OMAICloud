"""
Tool base classes and result types.

Every tool must:
  - Set class-level (or instance-level) name and description attributes
  - Declare input_schema as a JSON-Schema-compatible dict
  - Declare permissions (frozenset of required capability strings)
  - Declare risk_level: 'low' | 'medium' | 'high' | 'critical'
  - Set timeout (seconds, 0 = no limit) and retry count
  - Implement run(**kwargs) -> ToolResult
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass
class ToolResult:
    """
    Standardised result returned by every tool.

    Attributes:
        ok: True if the tool completed without error.
        data: structured output on success (any JSON-serialisable value).
        error: human-readable error message on failure.
        metadata: optional dict with execution metadata (duration_ms, retries, etc.)
    """

    ok: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.ok


class Tool(ABC):
    """
    Abstract base for all OM-AI tools.

    Class-level attributes (can be overridden in __init__):
        name:         unique tool identifier (dot-namespaced, e.g. 'action.shell')
        description:  one-sentence description for planners and UIs
        input_schema: JSON Schema dict describing accepted kwargs
        permissions:  frozenset of capability strings required to run this tool
        risk_level:   impact severity of the tool
        timeout:      per-call timeout in seconds (0 = no timeout)
        retry:        number of extra retry attempts on failure
    """

    name: str = ""
    description: str = ""
    input_schema: dict = {}
    permissions: frozenset[str] = frozenset()
    risk_level: RiskLevel = "low"
    timeout: int = 30
    retry: int = 0

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool. Must return a ToolResult; must not raise."""
        ...

    def describe(self) -> dict:
        """Return a JSON-serialisable descriptor for admin/planner consumption."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "permissions": sorted(self.permissions),
            "risk_level": self.risk_level,
            "timeout": self.timeout,
            "retry": self.retry,
        }
