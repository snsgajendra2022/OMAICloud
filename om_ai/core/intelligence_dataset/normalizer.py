"""
OM Intelligence Dataset Normalizer.

Converts incoming dataset records into a consistent representation
before validation and persistence.
"""

from __future__ import annotations

import re
from typing import Any


class DatasetNormalizer:

    def normalize_text(
        self,
        value: Any,
    ) -> str:

        if value is None:
            return ""

        text = str(value)

        text = (
            text
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    def normalize_list(
        self,
        value: Any,
    ) -> list[str]:

        if value is None:
            return []

        if isinstance(value, str):

            value = value.strip()

            if not value:
                return []

            return [
                part.strip()
                for part in value.split(",")
                if part.strip()
            ]

        if isinstance(value, (list, tuple, set)):

            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        return [
            str(value).strip()
        ]

    def normalize(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:

        data = dict(record)

        text_fields = [
            "input_text",
            "ideal_response",
            "language",
            "intent",
            "meaning",
            "goal",
            "domain",
            "reasoning_strategy",
            "reasoning_summary",
            "verification_strategy",
            "source",
            "quality",
            "learning_status",
        ]

        for field in text_fields:

            if field in data:

                data[field] = self.normalize_text(
                    data[field]
                )

        for field in [
            "tags",
            "expected_actions",
        ]:

            if field in data:

                data[field] = self.normalize_list(
                    data[field]
                )

        return data