from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import math
import re


@dataclass
class QualityEvaluation:
    score: float
    approved: bool
    dimensions: dict[str, float]
    issues: list[str]
    signals: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QualityEvaluator:
    """
    OM teacher-response quality gate.

    Important:
    - Does not equate response length with quality.
    - Does not require long answers for simple questions.
    - Uses deterministic checks for corruption/leakage.
    - Accepts semantic/model-based evaluation when supplied.
    """

    def __init__(
        self,
        approval_threshold: float = 0.65,
    ) -> None:
        self.approval_threshold = approval_threshold

    def evaluate(
        self,
        question: str,
        answer: str,
        *,
        semantic_evaluation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        question = self._normalize(question)
        answer = self._normalize(answer)

        issues: list[str] = []

        if not answer:
            return QualityEvaluation(
                score=0.0,
                approved=False,
                dimensions={
                    "relevance": 0.0,
                    "completeness": 0.0,
                    "clarity": 0.0,
                    "coherence": 0.0,
                    "instruction_adherence": 0.0,
                },
                issues=["empty_response"],
                signals={},
            ).to_dict()

        signals = {
            "characters": len(answer),
            "words": len(answer.split()),
            "sentences": self._sentence_count(answer),
            "repetition_ratio": self._repetition_ratio(answer),
            "garbage_score": self._garbage_score(answer),
            "question_echo": self._is_question_echo(question, answer),
            "leakage": self._detect_leakage(answer),
            "malformed": self._is_malformed(answer),
        }

        if signals["garbage_score"] >= 0.65:
            issues.append("garbage_response")

        if signals["repetition_ratio"] >= 0.65:
            issues.append("excessive_repetition")

        if signals["question_echo"]:
            issues.append("question_echo")

        if signals["leakage"]:
            issues.append("internal_or_dataset_leakage")

        if signals["malformed"]:
            issues.append("malformed_response")

        heuristic_dimensions = self._heuristic_dimensions(
            question=question,
            answer=answer,
            signals=signals,
        )

        dimensions = dict(heuristic_dimensions)

        # Semantic evaluation should come from a local teacher/evaluator
        # during offline distillation.
        if semantic_evaluation:
            dimensions = self._merge_semantic_evaluation(
                dimensions,
                semantic_evaluation,
            )

            semantic_issues = semantic_evaluation.get("issues", [])

            if isinstance(semantic_issues, list):
                for issue in semantic_issues:
                    issue = str(issue).strip()

                    if issue and issue not in issues:
                        issues.append(issue)

        score = self._weighted_score(dimensions)

        # Hard failures override otherwise-good semantic scores.
        hard_failures = {
            "empty_response",
            "garbage_response",
            "internal_or_dataset_leakage",
            "malformed_response",
        }

        approved = (
            score >= self.approval_threshold
            and not any(issue in hard_failures for issue in issues)
        )

        return QualityEvaluation(
            score=round(score, 4),
            approved=approved,
            dimensions={
                key: round(value, 4)
                for key, value in dimensions.items()
            },
            issues=issues,
            signals=signals,
        ).to_dict()

    def _heuristic_dimensions(
        self,
        *,
        question: str,
        answer: str,
        signals: dict[str, Any],
    ) -> dict[str, float]:

        clarity = self._clarity_score(answer)

        coherence = self._coherence_score(
            answer,
            signals,
        )

        relevance = self._lexical_relevance(
            question,
            answer,
        )

        completeness = self._completeness_score(
            question,
            answer,
        )

        instruction_adherence = self._instruction_adherence_score(
            question,
            answer,
        )

        return {
            "relevance": relevance,
            "completeness": completeness,
            "clarity": clarity,
            "coherence": coherence,
            "instruction_adherence": instruction_adherence,
        }

    def _merge_semantic_evaluation(
        self,
        heuristic: dict[str, float],
        semantic: dict[str, Any],
    ) -> dict[str, float]:

        result = dict(heuristic)

        semantic_dimensions = semantic.get(
            "dimensions",
            semantic,
        )

        if not isinstance(semantic_dimensions, dict):
            return result

        for key in result:
            if key not in semantic_dimensions:
                continue

            try:
                semantic_score = float(
                    semantic_dimensions[key]
                )
            except (TypeError, ValueError):
                continue

            semantic_score = self._clamp(
                semantic_score
            )

            # Semantic judgement gets more weight than
            # shallow deterministic heuristics.
            result[key] = (
                result[key] * 0.30
                + semantic_score * 0.70
            )

        return result

    def _weighted_score(
        self,
        dimensions: dict[str, float],
    ) -> float:

        weights = {
            "relevance": 0.30,
            "completeness": 0.25,
            "clarity": 0.15,
            "coherence": 0.20,
            "instruction_adherence": 0.10,
        }

        total = 0.0
        used_weight = 0.0

        for name, weight in weights.items():
            if name not in dimensions:
                continue

            total += (
                self._clamp(dimensions[name])
                * weight
            )

            used_weight += weight

        if used_weight == 0:
            return 0.0

        return self._clamp(
            total / used_weight
        )

    def _completeness_score(
        self,
        question: str,
        answer: str,
    ) -> float:
        """
        Completeness is not based on hitting an arbitrary
        character count.

        A concise response can receive a high score.
        """

        words = answer.split()

        if not words:
            return 0.0

        if len(words) <= 2:
            return 0.35

        if len(words) <= 5:
            return 0.60

        # A meaningful sentence can already be complete.
        if self._sentence_count(answer) >= 1:
            base = 0.82
        else:
            base = 0.70

        # Multi-part user requests require more evidence of coverage.
        requested_parts = self._estimate_request_complexity(
            question
        )

        answer_units = max(
            self._sentence_count(answer),
            self._list_item_count(answer),
            1,
        )

        if requested_parts > 1:
            coverage = min(
                answer_units / requested_parts,
                1.0,
            )

            base = (
                base * 0.60
                + coverage * 0.40
            )

        return self._clamp(base)

    def _clarity_score(
        self,
        answer: str,
    ) -> float:

        if not answer.strip():
            return 0.0

        score = 1.0

        words = answer.split()

        if words:
            average_word_length = (
                sum(len(word) for word in words)
                / len(words)
            )

            if average_word_length > 18:
                score -= 0.15

        if self._has_excessive_punctuation(answer):
            score -= 0.20

        if self._has_broken_spacing(answer):
            score -= 0.15

        return self._clamp(score)

    def _coherence_score(
        self,
        answer: str,
        signals: dict[str, Any],
    ) -> float:

        score = 1.0

        score -= (
            signals["repetition_ratio"]
            * 0.45
        )

        score -= (
            signals["garbage_score"]
            * 0.55
        )

        return self._clamp(score)

    def _lexical_relevance(
        self,
        question: str,
        answer: str,
    ) -> float:
        """
        This is only a weak fallback signal.

        It must NOT be treated as semantic understanding.
        """

        q_tokens = self._meaningful_tokens(question)
        a_tokens = self._meaningful_tokens(answer)

        if not q_tokens:
            return 0.75

        overlap = len(
            q_tokens.intersection(a_tokens)
        )

        ratio = overlap / max(
            len(q_tokens),
            1,
        )

        # Do not punish paraphrases too aggressively.
        return self._clamp(
            0.65 + min(ratio, 1.0) * 0.35
        )

    def _instruction_adherence_score(
        self,
        question: str,
        answer: str,
    ) -> float:

        if not answer:
            return 0.0

        # Without semantic evaluation we cannot reliably
        # determine instruction adherence.
        # Use neutral-positive fallback rather than fake certainty.
        return 0.75

    def _repetition_ratio(
        self,
        text: str,
    ) -> float:

        tokens = [
            token.lower()
            for token in re.findall(
                r"\b[\w'-]+\b",
                text,
            )
        ]

        if len(tokens) < 12:
            return 0.0

        bigrams = list(
            zip(tokens, tokens[1:])
        )

        if not bigrams:
            return 0.0

        duplicate_count = (
            len(bigrams)
            - len(set(bigrams))
        )

        return self._clamp(
            duplicate_count
            / len(bigrams)
        )

    def _garbage_score(
        self,
        text: str,
    ) -> float:

        if not text:
            return 1.0

        tokens = text.split()

        if not tokens:
            return 1.0

        suspicious = 0

        for token in tokens:
            clean = re.sub(
                r"[^\w'-]",
                "",
                token,
            )

            if not clean:
                continue

            if len(clean) >= 30:
                suspicious += 1
                continue

            letters = sum(
                ch.isalpha()
                for ch in clean
            )

            digits = sum(
                ch.isdigit()
                for ch in clean
            )

            if (
                letters > 0
                and digits > 0
                and len(clean) > 18
            ):
                suspicious += 1

        ratio = suspicious / max(
            len(tokens),
            1,
        )

        return self._clamp(
            ratio * 3.0
        )

    def _detect_leakage(
        self,
        text: str,
    ) -> bool:

        patterns = [
            r"\[tool:[^\]]+\]",
            r"<\|system\|>",
            r"<\|assistant\|>",
            r"<\|tool\|>",
            r"\bsource\s*:\s*[^\n]+\.jsonl\b",
            r"\bdomain\s*:[^\n]+\|\s*source\s*:",
            r"\bOPENAI_API_KEY\s*=",
            r"\bANTHROPIC_API_KEY\s*=",
            r"\bGOOGLE_API_KEY\s*=",
            r"\bXAI_API_KEY\s*=",
        ]

        return any(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            for pattern in patterns
        )

    def _is_question_echo(
        self,
        question: str,
        answer: str,
    ) -> bool:

        q = self._normalize(question).lower()
        a = self._normalize(answer).lower()

        if not q or not a:
            return False

        if q == a:
            return True

        if len(q) >= 20 and a.startswith(q):
            remaining = a[len(q):].strip()

            return len(remaining) < 10

        return False

    def _is_malformed(
        self,
        text: str,
    ) -> bool:

        if "\x00" in text:
            return True

        replacement_count = text.count("\ufffd")

        if replacement_count >= 3:
            return True

        return False

    def _estimate_request_complexity(
        self,
        question: str,
    ) -> int:

        if not question:
            return 1

        parts = 1

        parts += question.count("?")

        numbered = re.findall(
            r"(?:^|\n)\s*\d+[.)]\s+",
            question,
        )

        bullets = re.findall(
            r"(?:^|\n)\s*[-*]\s+",
            question,
        )

        parts += len(numbered)
        parts += len(bullets)

        # Keep this only as structural analysis.
        return max(1, min(parts, 10))

    def _sentence_count(
        self,
        text: str,
    ) -> int:

        chunks = re.split(
            r"(?<=[.!?])\s+|\n+",
            text.strip(),
        )

        return len(
            [
                chunk
                for chunk in chunks
                if chunk.strip()
            ]
        )

    def _list_item_count(
        self,
        text: str,
    ) -> int:

        return len(
            re.findall(
                r"(?:^|\n)\s*(?:[-*]|\d+[.)])\s+",
                text,
            )
        )

    def _meaningful_tokens(
        self,
        text: str,
    ) -> set[str]:

        tokens = re.findall(
            r"\b[a-zA-Z0-9_+#.-]{2,}\b",
            text.lower(),
        )

        stop = {
            "the",
            "and",
            "for",
            "are",
            "was",
            "were",
            "what",
            "why",
            "how",
            "when",
            "where",
            "who",
            "this",
            "that",
            "with",
            "from",
            "into",
            "can",
            "could",
            "would",
            "should",
            "please",
            "explain",
        }

        return {
            token
            for token in tokens
            if token not in stop
        }

    def _has_excessive_punctuation(
        self,
        text: str,
    ) -> bool:

        punctuation = re.findall(
            r"[!?.,;:]{4,}",
            text,
        )

        return bool(punctuation)

    def _has_broken_spacing(
        self,
        text: str,
    ) -> bool:

        return bool(
            re.search(
                r" {5,}",
                text,
            )
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        return " ".join(
            str(value or "").split()
        )

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:

        if not math.isfinite(value):
            return 0.0

        return max(
            0.0,
            min(float(value), 1.0),
        )