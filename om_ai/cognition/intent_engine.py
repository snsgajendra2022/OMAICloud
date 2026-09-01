"""
OM AI Intent Understanding Engine

Purpose:
- Understand user intention before RAG retrieval
- Detect domain
- Detect task type
- Detect technology context

This prevents wrong knowledge retrieval.
"""
from __future__ import annotations

import re

from om_ai.understanding.query_kind import query_kind


def _has(text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text))


class IntentEngine:
    def __init__(self) -> None:
        pass

    def analyze(self, text: str) -> dict:
        """Analyze user message and extract intent."""
        text_lower = (text or "").lower()
        kind = query_kind(text)

        intent = {
            "domain": "general",
            "task": "question",
            "technology": None,
            "language": None,
        }

        if kind == "greeting":
            intent["task"] = "greeting"
            return intent
        if kind == "knowledge":
            intent["domain"] = "knowledge"
            intent["task"] = "question"
            return intent
        if kind == "business":
            intent["domain"] = "business"
            intent["task"] = "analysis"
            return intent

        programming_keywords = [
            "code",
            "coding",
            "program",
            "react",
            "react native",
            "vue",
            "angular",
            "python",
            "java",
            "php",
            "laravel",
            "fastapi",
            "api",
            "database",
            "sql",
            "docker",
        ]
        if any(_has(text_lower, keyword) for keyword in programming_keywords):
            intent["domain"] = "programming"

        development_keywords = [
            "create",
            "build",
            "develop",
            "make",
            "implement",
            "fix",
        ]
        if any(_has(text_lower, keyword) for keyword in development_keywords):
            intent["task"] = "development"

        if _has(text_lower, "react native"):
            intent["technology"] = "React Native"
        elif _has(text_lower, "react"):
            intent["technology"] = "React"
        elif _has(text_lower, "fastapi"):
            intent["technology"] = "FastAPI"
        elif _has(text_lower, "python"):
            intent["technology"] = "Python"
        elif _has(text_lower, "laravel"):
            intent["technology"] = "Laravel"

        languages = {
            "javascript": "JavaScript",
            "typescript": "TypeScript",
            "python": "Python",
            "java": "Java",
            "php": "PHP",
            "c#": "C#",
        }
        for key, value in languages.items():
            if _has(text_lower, key):
                intent["language"] = value
                break

        return intent
