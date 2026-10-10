from dataclasses import dataclass,field
from typing import Any
@dataclass
class ConversationTurn:
    role:str; content:str; intent:str=""; relation:str=""; topic:str=""; task:str=""
@dataclass
class ConversationState:
    conversation_id:str; tenant_id:str="default"; actor:str=""; current_topic:str=""; active_task:str=""; active_goal:str=""
    last_user_message:str=""; last_assistant_message:str=""; last_assistant_question:str=""
    unresolved_questions:list[str]=field(default_factory=list); entities:dict[str,str]=field(default_factory=dict)
    recent_messages:list[ConversationTurn]=field(default_factory=list); references:list[dict[str,Any]]=field(default_factory=list)
    def add(self,turn:ConversationTurn,limit:int=24):
        self.recent_messages=(self.recent_messages+[turn])[-limit:]
        if turn.role=="user": self.last_user_message=turn.content
        if turn.role=="assistant": self.last_assistant_message=turn.content
