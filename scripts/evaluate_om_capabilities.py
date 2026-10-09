#!/usr/bin/env python3
"""Run a reproducible native-only OM capability smoke evaluation.

This is a small regression smoke test, not a standardized benchmark or a parity claim.
It never calls a hosted LLM. Selected tasks use deterministic, intentionally simple
checks; all saved answers remain available for human review.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from om_ai.backends.om_native import OMNativeBackend, default_native_paths
from om_ai.runtime.engine import is_degenerate_generation


CASES = [
    ("conversation", "Introduce OM AI in one sentence."),
    ("instruction_following", "Give exactly three numbered tips for clearer writing."),
    ("knowledge", "Explain why the sky looks blue to a 10-year-old."),
    ("math", "Calculate 17 * 23. Show the arithmetic and final answer."),
    ("logic", "All zargs are wugs. Some wugs are red. Can we conclude that some zargs are red? Explain."),
    ("planning", "Make a practical 4-step plan to learn Python for 30 minutes a day."),
    ("coding", "Write a Python function is_palindrome(text) that ignores spaces and letter case, then include two assert tests."),
    ("debugging", "Find and fix the bug in this Python function: def add(a, b): return str(a + b). Explain the issue."),
    ("structured_output", "Return valid JSON with keys \"name\" and \"skills\". Set name to \"OM\" and skills to a list containing \"chat\" and \"coding\". Output JSON only."),
    ("uncertainty", "What will the exact weather be at my home one month from today? Explain what information or tools are needed instead of inventing a forecast."),
    ("context_retention", "Remember this code word for the next turn only: MAPLE-731. Reply with just: saved."),
    ("tool_awareness", "You need to read a file on my computer, but no file was attached and no filesystem tool is available in this chat. What should you do?"),
]


def deterministic_checks(category: str, answer: str) -> dict[str, bool]:
    """Return transparent smoke checks; these are not semantic-quality judgments."""
    text = answer or ""
    normalized = text.lower()
    checks: dict[str, bool] = {}

    if category == "conversation":
        checks["one_sentence_like"] = 1 <= len(re.findall(r"[.!?](?:['\"”)]*)?(?:\s|$)", text)) <= 2
        checks["mentions_om"] = "om" in normalized
    elif category == "instruction_following":
        numbered = re.findall(r"(?m)^\s*(?:\d+[.)]|[-*])\s+\S", text)
        checks["exactly_three_list_items"] = len(numbered) == 3
    elif category == "knowledge":
        checks["mentions_light_scattering"] = any(
            phrase in normalized for phrase in ("scatter", "scattering", "scatters")
        )
        checks["mentions_blue_light_or_wavelength"] = "blue" in normalized and any(
            phrase in normalized for phrase in ("light", "wavelength", "shorter")
        )
    elif category == "math":
        checks["contains_391"] = bool(re.search(r"(?<!\d)391(?!\d)", text))
    elif category == "logic":
        checks["rejects_invalid_conclusion"] = any(
            phrase in normalized for phrase in (
                "cannot conclude", "can't conclude", "not necessarily",
                "does not follow", "cannot be concluded", "not enough information",
                "doesn't follow", "no conclusion"
            )
        )
    elif category == "planning":
        numbered = re.findall(r"(?m)^\s*\d+[.)]\s+\S", text)
        checks["four_numbered_steps"] = len(numbered) == 4
        checks["mentions_python_or_practice"] = "python" in normalized or "practice" in normalized
    elif category == "coding":
        checks["contains_function_name"] = "is_palindrome" in text
        checks["contains_at_least_two_asserts"] = len(re.findall(r"(?m)^\s*assert\b", text)) >= 2
        checks["mentions_case_or_lowercase"] = any(
            phrase in normalized for phrase in ("lower()", "case", "lowercase", "casefold()")
        )
    elif category == "debugging":
        checks["fixes_string_return"] = bool(
            re.search(r"(?m)^\s*return\s+a\s*\+\s*b\s*(?:#.*)?$", text)
        )
        checks["explains_string_type_issue"] = any(
            phrase in normalized for phrase in ("string", "str(", "type")
        )
    elif category == "structured_output":
        try:
            parsed = json.loads(text)
            checks["valid_json_with_expected_values"] = (
                isinstance(parsed, dict)
                and parsed.get("name") == "OM"
                and parsed.get("skills") == ["chat", "coding"]
            )
        except (json.JSONDecodeError, TypeError):
            checks["valid_json_with_expected_values"] = False
    elif category == "uncertainty":
        checks["does_not_claim_exact_forecast"] = any(
            phrase in normalized for phrase in (
                "can't know", "cannot know", "can't predict", "cannot predict",
                "not possible", "need your location", "weather forecast", "live weather",
                "check a weather service", "weather tool", "i don't have access"
            )
        )
    elif category == "context_retention":
        checks["acknowledges_saved"] = "saved" in normalized
    elif category == "tool_awareness":
        checks["asks_for_file_or_access"] = any(
            phrase in normalized for phrase in (
                "upload the file", "attach the file", "please upload", "please attach",
                "provide the file", "share the file", "need access", "can't access",
                "cannot access", "no file was attached"
            )
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/evaluations/om-capability-smoke.json")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()

    if args.max_new_tokens < 1:
        parser.error("--max-new-tokens must be greater than zero")

    paths = default_native_paths()
    required = ("config", "tokenizer", "checkpoint")
    missing = [
        {"asset": key, "path": paths.get(key)}
        for key in required
        if not paths.get(key) or not Path(paths[key]).is_file()
    ]
    if missing:
        print(json.dumps({
            "ok": False,
            "stage": "preflight",
            "backend": "om_native",
            "missing": missing,
            "hint": "Fix .env/exported OM_MODEL_* paths; use a config, tokenizer and checkpoint from the same trained run.",
        }, indent=2))
        return 2

    backend = OMNativeBackend()
    try:
        load_info = backend.load(require_checkpoint=True)
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "stage": "load",
            "backend": "om_native",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, indent=2))
        return 2

    results = []
    failures = 0
    total_generation_seconds = 0.0
    conversation: list[dict[str, str]] = []
    for category, prompt in CASES:
        messages = conversation + [{"role": "user", "content": prompt}] if category == "context_retention" else [{"role": "user", "content": prompt}]
        started = time.perf_counter()
        try:
            answer = backend.chat(
                messages,
                max_new_tokens=args.max_new_tokens,
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.1,
                min_new_tokens=4,
            )
            elapsed = round(time.perf_counter() - started, 3)
            total_generation_seconds += elapsed
            usable = bool((answer or "").strip()) and not is_degenerate_generation(answer)
            correctness = deterministic_checks(category, answer or "")
            passed_checks = all(correctness.values()) if correctness else True
            ok = usable and passed_checks
            if not ok:
                failures += 1
            results.append({
                "category": category,
                "ok": ok,
                "usable_output": usable,
                "correctness_checks": correctness,
                "elapsed_seconds": elapsed,
                "prompt": prompt,
                "answer": (answer or "")[:4000],
            })
            if category == "context_retention":
                conversation = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer or ""},
                    {"role": "user", "content": "What was the code word I asked you to remember? Reply with the code word only."},
                ]
                started = time.perf_counter()
                followup = backend.chat(
                    conversation,
                    max_new_tokens=48,
                    temperature=0.0,
                    top_p=0.9,
                    top_k=40,
                    repetition_penalty=1.1,
                    min_new_tokens=1,
                )
                followup_elapsed = round(time.perf_counter() - started, 3)
                total_generation_seconds += followup_elapsed
                followup_ok = (
                    bool((followup or "").strip())
                    and not is_degenerate_generation(followup)
                    and "MAPLE-731" in (followup or "")
                )
                if not followup_ok:
                    failures += 1
                results.append({
                    "category": "context_retention_followup",
                    "ok": followup_ok,
                    "usable_output": bool((followup or "").strip()) and not is_degenerate_generation(followup),
                    "elapsed_seconds": followup_elapsed,
                    "prompt": conversation[-1]["content"],
                    "answer": (followup or "")[:1000],
                    "expected_contains": "MAPLE-731",
                    "contains_expected": "MAPLE-731" in (followup or ""),
                })
        except Exception as exc:
            failures += 1
            elapsed = round(time.perf_counter() - started, 3)
            total_generation_seconds += elapsed
            results.append({
                "category": category,
                "ok": False,
                "usable_output": False,
                "elapsed_seconds": elapsed,
                "prompt": prompt,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    passed = sum(1 for item in results if item.get("ok"))
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "om_native",
        "provider": "OM AI",
        "hosted_fallback_used": False,
        "load": {
            "device": load_info.get("device"),
            "parameters": load_info.get("parameters"),
            "checkpoint": load_info.get("checkpoint"),
            "tokenizer_fingerprint": load_info.get("tokenizer_fingerprint"),
        },
        "case_count": len(results),
        "passed_case_count": passed,
        "failed_case_count": len(results) - passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "total_generation_seconds": round(total_generation_seconds, 3),
        "usable_output_count": sum(1 for item in results if item.get("usable_output")),
        "note": (
            "Smoke evaluation only, not a standardized benchmark or cloud-model parity claim. "
            "Deterministic checks are intentionally simple and can produce false negatives; "
            "inspect saved prompts, answers and checks before drawing quality conclusions."
        ),
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": failures == 0,
        "report": str(output),
        "case_count": len(results),
        "passed_case_count": passed,
        "failed_case_count": len(results) - passed,
        "pass_rate": report["pass_rate"],
        "total_generation_seconds": report["total_generation_seconds"],
        "hosted_fallback_used": False,
    }, indent=2))
    return 0 if failures == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
