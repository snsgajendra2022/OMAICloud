from dataclasses import dataclass, field


@dataclass
class IntentState:

    intent: str = "unknown"

    confidence: float = 0.0

    entities: dict = field(default_factory=dict)

    requires_tool: bool = False

    tool_name: str | None = None

    context: dict = field(default_factory=dict)

    response_style: str = "normal"