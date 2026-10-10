"""
OM Intelligence Dataset Schema.

Defines the canonical dataset contract.
"""

from __future__ import annotations

from typing import Any

from .dataset_item import DatasetItem


REQUIRED_FIELDS = (
    "input_text",
    "ideal_response",
    "dataset_type",
    "language",
    "intent",
)


def dataset_schema() -> dict[str, Any]:
    """
    Return the canonical dataset schema description.
    """

    return {

        "version": "1.0",

        "required": list(
            REQUIRED_FIELDS
        ),

        "fields": {

            "input_text": {
                "type": "string",
                "description":
                    "Original user input."
            },

            "ideal_response": {
                "type": "string",
                "description":
                    "High-quality target response."
            },

            "dataset_type": {
                "type": "string",
                "description":
                    "Intelligence category."
            },

            "language": {
                "type": "string",
                "description":
                    "Input language."
            },

            "intent": {
                "type": "string",
                "description":
                    "User intent."
            },

            "meaning": {
                "type": "string",
                "description":
                    "Semantic meaning."
            },

            "goal": {
                "type": "string",
                "description":
                    "User's underlying goal."
            },

            "domain": {
                "type": "string",
                "description":
                    "Knowledge/domain category."
            },

            "context": {
                "type": "object",
                "description":
                    "Conversation context."
            },

            "reasoning_strategy": {
                "type": "string",
                "description":
                    "Preferred reasoning approach."
            },

            "verification_strategy": {
                "type": "string",
                "description":
                    "How the answer should be checked."
            },

            "quality_score": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
        },
    }


def serialize_item(
    item: DatasetItem,
) -> dict[str, Any]:

    return item.to_dict()