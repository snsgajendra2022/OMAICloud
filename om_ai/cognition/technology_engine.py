"""OM-1.0 Technology Understanding Engine.

Structured stack detection only — not answer generation.
Longest phrase wins so "react native" is not collapsed to "react".
"""
from __future__ import annotations

import re
from typing import Any


class TechnologyEngine:
    def __init__(self) -> None:
        self.stack_map: dict[str, dict[str, Any]] = {
            "react native": {
                "category": "mobile",
                "language": "JavaScript",
                "platform": "android_ios",
            },
            "spring boot": {
                "category": "backend",
                "language": "Java",
                "platform": "api",
            },
            "next.js": {
                "category": "frontend",
                "language": "TypeScript",
                "platform": "web",
            },
            "nextjs": {
                "category": "frontend",
                "language": "TypeScript",
                "platform": "web",
            },
            "fastapi": {
                "category": "backend",
                "language": "Python",
                "platform": "api",
            },
            "laravel": {
                "category": "backend",
                "language": "PHP",
                "platform": "web_api",
            },
            "flutter": {
                "category": "mobile",
                "language": "Dart",
                "platform": "android_ios",
            },
            "kubernetes": {
                "category": "devops",
                "language": None,
                "platform": "orchestration",
            },
            "postgresql": {
                "category": "database",
                "language": None,
                "platform": "database",
            },
            "angular": {
                "category": "frontend",
                "language": "TypeScript",
                "platform": "web",
            },
            "docker": {
                "category": "devops",
                "language": None,
                "platform": "container",
            },
            "mysql": {
                "category": "database",
                "language": None,
                "platform": "database",
            },
            "react": {
                "category": "frontend",
                "language": "JavaScript",
                "platform": "web",
            },
            "vue": {
                "category": "frontend",
                "language": "JavaScript",
                "platform": "web",
            },
        }

    def analyze(self, text: str) -> dict[str, Any]:
        text_lower = (text or "").lower()
        result: dict[str, Any] = {
            "technology": None,
            "category": "unknown",
            "language": None,
            "platform": None,
            "confidence": 0,
        }
        for tech, info in sorted(self.stack_map.items(), key=lambda kv: len(kv[0]), reverse=True):
            if re.search(rf"(?<![a-z0-9]){re.escape(tech)}(?![a-z0-9])", text_lower):
                result["technology"] = tech
                result["category"] = info["category"]
                result["language"] = info["language"]
                result["platform"] = info["platform"]
                result["confidence"] = 1.0
                break
        return result
