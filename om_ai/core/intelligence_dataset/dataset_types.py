"""
OM Intelligence Dataset Types.

Central enums used by the dataset system.
"""

from __future__ import annotations

from enum import Enum


class DatasetType(str, Enum):
    GENERAL_QA = "general_qa"
    CONVERSATION = "conversation"
    REASONING = "reasoning"
    CODING = "coding"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    EMOTIONAL = "emotional"
    ACTION = "action"
    TOOL_USE = "tool_use"
    MULTILINGUAL = "multilingual"
    CORRECTION = "correction"


class DatasetSource(str, Enum):
    HUMAN = "human"
    SYNTHETIC = "synthetic"
    USER_FEEDBACK = "user_feedback"
    SYSTEM = "system"
    IMPORTED = "imported"
    RESEARCH = "research"


class QualityLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class LearningStatus(str, Enum):
    NEW = "new"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    LEARNED = "learned"