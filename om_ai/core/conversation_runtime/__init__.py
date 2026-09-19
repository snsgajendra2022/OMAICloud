"""STEP 52 — Continuous Human Conversation Runtime."""
from .conversational_flow import ConversationalFlow
from .response_timing import ResponseTiming

__all__ = ["ConversationalFlow", "ResponseTiming", "get_conversation_runtime"]

_RT = None

def get_conversation_runtime():
    global _RT
    if _RT is None:
        from .conversation_runtime import ConversationRuntime
        _RT = ConversationRuntime()
    return _RT
