from __future__ import annotations
from typing import Any


class ThoughtManager:
    """Internal thoughts / working notes before speaking (activity stream)."""

    def think(self, goal: dict[str, Any], awareness: dict[str, Any]) -> list[dict[str, str]]:
        thoughts: list[dict[str, str]] = [
            {"id": "voice", "label": "Voice activated"},
            {"id": "understand", "label": "Understanding request"},
        ]
        if awareness.get("has_memory"):
            thoughts.append({"id": "memory", "label": "Checking memory"})
        intent = goal.get("intent")
        if intent == "diagnose_and_plan":
            thoughts.extend(
                [
                    {"id": "scan", "label": "Scanning project signals"},
                    {"id": "hypotheses", "label": "Forming hypotheses"},
                    {"id": "plan", "label": "Building analysis plan"},
                ]
            )
        elif intent == "emotional_support":
            thoughts.append({"id": "empathy", "label": "Adjusting tone — concerned"})
        elif intent == "inspect_screen":
            thoughts.append({"id": "vision", "label": "Preparing vision pass"})
        elif intent == "create_reminder":
            thoughts.append({"id": "schedule", "label": "Parsing time and task"})
        else:
            thoughts.append({"id": "reply", "label": "Preparing response"})
        return thoughts
