from dataclasses import dataclass


@dataclass
class ConversationPattern:

    intent: str

    examples: list[str]