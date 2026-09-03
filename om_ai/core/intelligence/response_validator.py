"""Validate that the answer matches understanding — reject echoes and wrong intents."""
from __future__ import annotations

import re
from typing import Any


class ResponseValidator:
    def validate(
        self,
        question: str,
        answer: str,
        *,
        understanding: dict[str, Any],
        intent: dict[str, Any],
        capability: dict[str, Any],
    ) -> dict[str, Any]:
        q = (question or "").strip()
        a = (answer or "").strip()
        issues: list[str] = []
        score = 100.0

        if not a:
            return self._fail(["empty answer"], 0.0)

        # Never repeat the user message as the answer
        if self._is_echo(q, a):
            return self._fail(["echoed user message"], 10.0)

        # Ban useless "Understood: …" style meta
        if re.match(r"(?i)^(understood|i understand you want|you said)\b", a):
            if len(a) < max(40, len(q) + 20):
                issues.append("meta restatement without answer")
                score -= 40

        intent_name = str(understanding.get("intent") or intent.get("intent") or "")
        cap = str(capability.get("capability") or "")

        checks = {
            "date_request": lambda: bool(re.search(r"\d{4}|monday|tuesday|wednesday|thursday|friday|saturday|sunday", a, re.I)),
            "prompt_generation": lambda: "prompt" in a.lower() and len(a) > 80,
            "recommendation": lambda: any(x in a.lower() for x in ("playlist", "suggest", "recommend", "ideas", "-")),
            "conversation": lambda: len(a) > 10,
        }
        checker = checks.get(intent_name)
        if checker and not checker():
            issues.append(f"answer misses intent:{intent_name}")
            score -= 45

        # Wrong capability smell: coding wall of text for prompt intent without "prompt"
        if intent_name == "prompt_generation" and "prompt" not in a.lower():
            issues.append("prompt intent without prompt content")
            score -= 50

        if intent_name == "date_request" and "understood" in a.lower() and "date is" not in a.lower():
            issues.append("date intent not answered")
            score -= 50

        useful = len(a) >= 20 or intent_name in {"conversation", "date_request"}
        if not useful:
            issues.append("not useful")
            score -= 25

        needs_clarification = bool(understanding.get("needs_clarification")) or score < 55
        if intent.get("needs_clarification"):
            needs_clarification = True

        score = max(0.0, min(100.0, score))
        passed = score >= 75 and not any("echo" in i for i in issues)
        return {
            "passed": passed,
            "score": score,
            "issues": issues,
            "understood": intent_name not in {"unclear", ""},
            "answered_actual_question": passed,
            "useful": useful,
            "needs_clarification": needs_clarification and not passed,
            "capability": cap,
        }

    def _fail(self, issues: list[str], score: float) -> dict[str, Any]:
        return {
            "passed": False,
            "score": score,
            "issues": issues,
            "understood": False,
            "answered_actual_question": False,
            "useful": False,
            "needs_clarification": True,
        }

    def _is_echo(self, question: str, answer: str) -> bool:
        q = re.sub(r"\W+", " ", question.lower()).strip()
        a = re.sub(r"\W+", " ", answer.lower()).strip()
        if not q or not a:
            return False
        if a == q:
            return True
        if a in {f"understood {q}", f"understanding {q}", f"i understand {q}"}:
            return True
        # Answer mostly restates question
        if q in a and len(a) <= len(q) + 24:
            return True
        return False
