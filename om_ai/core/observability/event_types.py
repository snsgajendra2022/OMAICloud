from enum import Enum


class ActivityType(Enum):

    USER_REQUEST = "user_request"

    AGENT_START = "agent_start"

    AGENT_COMPLETE = "agent_complete"

    TOOL_CALL = "tool_call"

    SEARCH = "search"

    FILE_OPERATION = "file_operation"

    KNOWLEDGE_LOOKUP = "knowledge_lookup"

    MEMORY_ACCESS = "memory_access"

    MODEL_CALL = "model_call"

    DATASET_OPERATION = "dataset_operation"

    ERROR = "error"

    RESPONSE = "response"