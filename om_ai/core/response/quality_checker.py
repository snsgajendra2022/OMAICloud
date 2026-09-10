from __future__ import annotations

import math
import re
from collections import Counter


class QualityChecker:

    def validate(
        self,
        response: str | None = None,
        original_message: str = "",
        **kwargs,
    ) -> dict:

        if response is None and "response" in kwargs:
            response = kwargs.pop("response")
        if not original_message and "original_message" in kwargs:
            original_message = str(kwargs.pop("original_message") or "")

        text = (response or "").strip()

        issues: list[str] = []

        if not text:
            issues.append("empty_response")

            return {
                "approved": False,
                "score": 0.0,
                "issues": issues,
            }

        words = re.findall(
            r"\b[\w'-]+\b",
            text,
            flags=re.UNICODE,
        )

        if not words:
            issues.append("no_readable_words")

        if len(words) <= 2:
            issues.append("too_short")

        replacement_chars = text.count("�")

        if replacement_chars:
            issues.append(
                "tokenizer_replacement_characters"
            )

        # Excessive weird token mixing.
        weird_words = 0

        for word in words:
            if len(word) > 35:
                weird_words += 1
                continue

            uppercase = sum(
                1 for char in word if char.isupper()
            )

            lowercase = sum(
                1 for char in word if char.islower()
            )

            if (
                uppercase >= 3
                and lowercase >= 3
                and not word.isupper()
            ):
                weird_words += 1

        weird_ratio = (
            weird_words / max(len(words), 1)
        )

        if weird_ratio > 0.12:
            issues.append(
                "probable_garbage_generation"
            )

        # Vocabulary diversity can become abnormally high
        # in incoherent random-token output.
        lowered = [
            word.lower()
            for word in words
        ]

        unique_ratio = (
            len(set(lowered))
            / max(len(lowered), 1)
        )

        if (
            len(words) > 80
            and unique_ratio > 0.94
        ):
            issues.append(
                "abnormally_random_vocabulary"
            )

        # Sentence sanity.
        sentences = [
            part.strip()
            for part in re.split(
                r"[.!?।]+",
                text,
            )
            if part.strip()
        ]

        if (
            len(words) > 100
            and len(sentences) <= 1
        ):
            issues.append(
                "unstructured_generation"
            )

        severe = {
            "empty_response",
            "no_readable_words",
            "tokenizer_replacement_characters",
            "probable_garbage_generation",
            "abnormally_random_vocabulary",
        }

        severe_count = len(
            severe.intersection(issues)
        )

        score = 1.0

        score -= severe_count * 0.35
        score -= max(
            0,
            len(issues) - severe_count
        ) * 0.1

        score = max(
            0.0,
            min(score, 1.0),
        )

        return {
            "approved":
                severe_count == 0
                and score >= 0.55,

            "score": score,

            "issues": issues,
        }