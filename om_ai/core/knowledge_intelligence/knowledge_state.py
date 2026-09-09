from dataclasses import dataclass, field


@dataclass
class KnowledgeState:


    query: str


    retrieved_items:list = field(
        default_factory=list
    )


    research_plan:list = field(
        default_factory=list
    )


    confidence:float = 0.0