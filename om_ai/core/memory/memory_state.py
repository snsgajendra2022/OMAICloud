from dataclasses import dataclass, field


@dataclass
class MemoryState:


    current_context: list = field(
        default_factory=list
    )


    retrieved_memories: list = field(
        default_factory=list
    )


    new_memories: list = field(
        default_factory=list
    )


    confidence: float = 0.0