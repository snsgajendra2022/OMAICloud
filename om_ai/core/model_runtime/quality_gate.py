"""Quality gate enforcing generation safety and quality standards before output delivery."""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class QualityGateResult:
    passed: bool
    quality_score: float
    reason: str | None = None
    sanitized_text: str = ""
    checks: dict[str, bool] = field(default_factory=dict)


class GenerationQualityGate:
    """Rigorous 6-stage quality gate:
    1. Empty check
    2. Tokenizer / model corruption detection
    3. Garbage detection
    4. Repetition detection
    5. Context relevance & stub check
    6. Response quality scoring
    """

    _GENERIC_STUBS = re.compile(
        r"(?is)("
        r"the issue may come from incorrect assumptions|"
        r"the problem may be caused by environment or configuration|"
        r"the current approach may need redesign|"
        r"clarify goal, then give a direct actionable answer|"
        r"source\s*:\s*[\w\.\-]+\.jsonl|"
        r"domain\s*:\s*[\w\-]+\s*\|\s*source\s*:"
        r")"
    )

    def evaluate(
        self,
        raw_text: str | None,
        *,
        prompt: str = "",
        min_chars: int = 1,
    ) -> QualityGateResult:
        checks: dict[str, bool] = {
            "empty": False,
            "corruption": False,
            "garbage": False,
            "repetition": False,
            "relevance": False,
            "quality": False,
        }

        text = (raw_text or "").strip()

        # 1. Empty check
        if not text or len(text) < min_chars:
            return QualityGateResult(
                passed=False,
                quality_score=0.0,
                reason="empty_output",
                checks=checks,
            )
        checks["empty"] = True

        # 2. Corruption check
        if "\ufffd" in text:
            return QualityGateResult(
                passed=False,
                quality_score=0.0,
                reason="corruption_detected: unicode replacement char \ufffd present",
                checks=checks,
            )
        ctrl_chars = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
        if ctrl_chars > 0:
            return QualityGateResult(
                passed=False,
                quality_score=0.0,
                reason=f"corruption_detected: {ctrl_chars} control characters present",
                checks=checks,
            )
        checks["corruption"] = True

        # 3. Garbage check
        total_len = len(text)
        printable_count = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
        if printable_count / max(1, total_len) < 0.85:
            return QualityGateResult(
                passed=False,
                quality_score=0.0,
                reason="garbage_detected: unprintable ratio exceeds threshold",
                checks=checks,
            )

        alpha_count = sum(1 for c in text if c.isalpha())
        if total_len > 15 and (alpha_count / max(1, total_len)) < 0.20:
            if "{" not in text and ";" not in text and "<" not in text:
                return QualityGateResult(
                    passed=False,
                    quality_score=0.0,
                    reason="garbage_detected: insufficient natural language content",
                    checks=checks,
                )
        checks["garbage"] = True

        # 4. Repetition detection
        words = text.split()
        if len(words) >= 6:
            low_words = [w.lower() for w in words]
            for i in range(len(low_words) - 3):
                if low_words[i] == low_words[i+1] == low_words[i+2] == low_words[i+3]:
                    return QualityGateResult(
                        passed=False,
                        quality_score=0.0,
                        reason=f"repetition_detected: 4-token repeating loop on '{low_words[i]}'",
                        checks=checks,
                    )

            possessive_count = sum(1 for w in words if "'s" in w.lower() or "’s" in w.lower())
            if possessive_count / len(words) >= 0.18:
                return QualityGateResult(
                    passed=False,
                    quality_score=0.0,
                    reason="repetition_detected: possessive collapse loop",
                    checks=checks,
                )

            if len(words) > 20:
                unique_words = set(w.strip(".,!?:;\"'()[]{}").lower() for w in words)
                diversity_ratio = len(unique_words) / len(words)
                if diversity_ratio < 0.22:
                    return QualityGateResult(
                        passed=False,
                        quality_score=0.0,
                        reason=f"repetition_detected: vocabulary collapse (diversity {diversity_ratio:.2f})",
                        checks=checks,
                    )
        checks["repetition"] = True

        # 5. Context relevance & stub check
        if self._GENERIC_STUBS.search(text):
            return QualityGateResult(
                passed=False,
                quality_score=0.1,
                reason="relevance_failure: generic solution stub or dataset leak detected",
                checks=checks,
            )
        if prompt:
            p_words = set(re.findall(r"\w+", prompt.lower()))
            t_words = set(re.findall(r"\w+", text.lower()))
            if len(words) <= 10 and t_words and t_words.issubset(p_words):
                if not any(g in text.lower() for g in ("hello", "hi", "hey", "good morning", "good evening", "i'm om", "i am om")):
                    return QualityGateResult(
                        passed=False,
                        quality_score=0.1,
                        reason="relevance_failure: answer echoes prompt",
                        checks=checks,
                    )
        checks["relevance"] = True

        # 6. Response quality scoring
        score = 0.5
        if len(text) >= 20:
            score += 0.2
        if any(punct in text for punct in ".!?।\n"):
            score += 0.2
        if not re.search(r"[A-Z]{6,}", text):
            score += 0.1
        score = min(1.0, max(0.0, score))
        checks["quality"] = True

        return QualityGateResult(
            passed=True,
            quality_score=score,
            reason=None,
            sanitized_text=text,
            checks=checks,
        )


_DEFAULT_QUALITY_GATE: GenerationQualityGate | None = None


def get_quality_gate() -> GenerationQualityGate:
    global _DEFAULT_QUALITY_GATE
    if _DEFAULT_QUALITY_GATE is None:
        _DEFAULT_QUALITY_GATE = GenerationQualityGate()
    return _DEFAULT_QUALITY_GATE
