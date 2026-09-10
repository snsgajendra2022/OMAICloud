"""Self-critic for OM answers — empty, topic, repeats, leakage, garbage."""
from __future__ import annotations

import re


class SelfCritic:

    def review(self, question: str, answer: str) -> dict:
        issues: list[str] = []
        text = (answer or "").strip()
        q = (question or "").strip()
        overlap = 0.0

        if not text:
            issues.append("empty_answer")

        if text and len(text) < 20:
            issues.append("too_short")

        q_words = set(q.lower().split())
        a_words = set(text.lower().split())
        overlap = len(q_words.intersection(a_words)) / max(len(q_words), 1)
        if q_words and overlap < 0.05 and len(text.split()) > 8:
            # Allow structured research/greeting refusals
            if not any(
                m in text.lower()
                for m in (
                    "i detected this requires",
                    "according to verified",
                    "i can help generate text, but i will not",
                    "hello —",
                    "i'm om",
                )
            ):
                issues.append("possible_topic_mismatch")

        words = text.split()
        if len(words) >= 8:
            for n in (2, 3, 4):
                grams = [" ".join(words[i : i + n]) for i in range(len(words) - n)]
                if grams:
                    counts: dict[str, int] = {}
                    for g in grams:
                        counts[g] = counts.get(g, 0) + 1
                    if any(v >= 4 for v in counts.values()):
                        issues.append("repeated_output")
                        break

        leak_markers = (
            "question:",
            "answer:",
            ".jsonl",
            "training example",
            "dataset",
            "domain:",
        )
        low = text.lower()
        if any(m in low for m in leak_markers):
            issues.append("leaked_dataset")

        if words:
            unique_ratio = len(set(w.lower() for w in words)) / max(len(words), 1)
            if len(words) > 50 and unique_ratio > 0.9:
                issues.append("random_text")
            weird = sum(
                1
                for w in words
                if len(w) > 28 or re.search(r"[A-Z]{3,}[a-z]{3,}[A-Z]", w)
            )
            if weird / max(len(words), 1) > 0.15:
                issues.append("random_text")

        return {
            "approved": len(issues) == 0,
            "issues": issues,
            "overlap": overlap,
        }
