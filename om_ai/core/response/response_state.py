from dataclasses import dataclass, field


@dataclass
class ResponseState:

    user_message: str

    intent: str = "unknown"

    response_type: str = "text"

    instructions: list[str] = field(
        default_factory=list
    )

    draft_response: str = ""

    quality_score: float = 0.0

    approved: bool = False

    regenerate: bool = False