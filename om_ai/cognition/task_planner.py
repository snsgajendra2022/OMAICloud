"""
OM-1.0 Task Decomposition Engine

Purpose:
Break user requirements into smaller executable tasks.

Input:
    User request

Output:
    Goal + Task list
"""
from __future__ import annotations

import re

from om_ai.understanding.query_kind import query_kind


def _has(text: str, *phrases: str) -> bool:
    for phrase in phrases:
        if re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text):
            return True
    return False


class TaskPlanner:
    def __init__(self) -> None:
        pass

    def decompose(self, request: str) -> dict:
        text = (request or "").lower()
        result = {
            "goal": request,
            "category": "general",
            "tasks": [],
        }

        kind = query_kind(request)
        if kind in {"greeting", "knowledge"}:
            return result

        # Mobile application — specific screens when the request names them.
        if _has(text, "react native", "flutter", "mobile app", "android", "ios"):
            result["category"] = "mobile_application"
            if _has(text, "login") and _has(text, "dashboard"):
                result["tasks"] = [
                    "Create Login Screen",
                    "Create Dashboard Screen",
                    "Setup Navigation",
                    "Authentication",
                ]
            elif _has(text, "login"):
                result["tasks"] = [
                    "Create screen component",
                    "Add input fields",
                    "Add validation",
                    "Connect authentication API",
                    "Test on Android/iOS",
                ]
            else:
                result["tasks"] = [
                    "Setup mobile project structure",
                    "Create UI screens",
                    "Setup navigation",
                    "Implement authentication",
                    "Connect APIs",
                    "Add styling",
                    "Test application",
                ]

        # Web application
        elif _has(text, "react", "vue", "angular", "website", "web app"):
            result["category"] = "web_application"
            result["tasks"] = [
                "Setup frontend structure",
                "Create components",
                "Implement pages",
                "Connect APIs",
                "Add styling",
                "Test application",
            ]

        # Backend API
        elif _has(text, "api", "backend", "fastapi", "laravel", "spring boot"):
            result["category"] = "backend_system"
            result["tasks"] = [
                "Design API architecture",
                "Create database structure",
                "Implement endpoints",
                "Add authentication",
                "Add validation",
                "Write tests",
                "Deploy service",
            ]

        # AI system — word boundary so "ai" does not match inside "india"
        elif _has(text, "ai", "model", "agent", "llm"):
            result["category"] = "ai_system"
            result["tasks"] = [
                "Define AI architecture",
                "Prepare data pipeline",
                "Create model workflow",
                "Implement evaluation",
                "Deploy inference system",
            ]

        elif kind == "coding":
            result["tasks"] = [
                "Understand requirement",
                "Create implementation plan",
                "Develop solution",
                "Test result",
            ]

        return result
