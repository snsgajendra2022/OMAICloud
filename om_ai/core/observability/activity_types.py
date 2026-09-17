from enum import Enum


class ActivityType(Enum):

    THINKING = "thinking"

    SEARCHING = "searching"

    READING = "reading"

    ANALYZING = "analyzing"

    TOOL_USAGE = "tool_usage"

    KNOWLEDGE = "knowledge"

    RESEARCH = "research"

    MEMORY = "memory"

    AGENT = "agent"

    VALIDATION = "validation"

    RESPONSE = "response"

    COMPLETED = "completed"

    ERROR = "error"