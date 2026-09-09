from dataclasses import dataclass, field


@dataclass
class ReasoningState:


    problem: str

    analysis: dict = field(
        default_factory=dict
    )


    plan:list = field(
        default_factory=list
    )


    confidence:float = 0.0