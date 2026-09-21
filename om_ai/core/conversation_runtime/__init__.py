"""STEP 52/65 — Continuous + realtime human conversation runtime."""
from .conversational_flow import ConversationalFlow
from .response_timing import ResponseTiming
from .realtime_conversation import RealtimeConversation
from .conversation_loop import ConversationLoop

__all__ = [
    "ConversationalFlow",
    "ResponseTiming",
    "RealtimeConversation",
    "ConversationLoop",
    "get_conversation_runtime",
    "get_conversation_loop",
]

_RT = None
_LOOP = None


def get_conversation_runtime():
    global _RT
    if _RT is None:
        from .conversation_runtime import ConversationRuntime

        _RT = ConversationRuntime()
    return _RT


def get_conversation_loop() -> ConversationLoop:
    global _LOOP
    if _LOOP is None:
        _LOOP = ConversationLoop()
    return _LOOP
