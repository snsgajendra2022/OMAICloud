from dataclasses import dataclass, field



@dataclass
class ConversationState:


    session_id:str


    current_task:str = ""


    user_goal:str = ""


    active_topics:list[str] = field(
        default_factory=list
    )


    important_facts:list[str] = field(
        default_factory=list
    )