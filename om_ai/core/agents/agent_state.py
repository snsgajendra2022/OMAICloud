from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:

    task: str

    agent_name: str = ""

    result: Any = None

    confidence: float = 0.0

    completed: bool = False

    notes: list[str] = field(
        default_factory=list
    )