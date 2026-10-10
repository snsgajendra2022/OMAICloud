#!/usr/bin/env python3
"""Small, repeatable native OM chat evaluation harness.

This evaluates the exact checkpoint/config/tokenizer combination supplied by the
caller. It reports generation and obvious-degeneracy signals; it is not a
semantic benchmark and cannot certify factual correctness.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from om_ai.runtime.engine import LocalLLMEngine, is_degenerate_generation


DEFAULT_CASES = [
    {"id": "greeting", "messages": [{"role": "user", "content": "Hello! How are you?"}]},
    {"id": "explanation", "messages": [{"role": "user", "content": "Why does the sky appear blue? Explain simply."}]},
    {"id": "arithmetic", "messages": [{"role": "user", "content": "What is 17 multiplied by 23? Show the calculation."}], "must_contain": ["391"]},
    {"id": "coding", "messages": [{"role": "user", "content": "Write a Python function that returns the factorial of a non-negative integer."}], "must_contain_any": ["def ", "factorial"]},
    {"id": "hinglish", "messages": [{"role": "user", "content": "Mujhe simple English mein batao ki Python list kya hoti hai."}]},
    {"id": "followup", "messages": [{"role": "user", "content": "My name is Riya and I am learning Python."}, {"role": "assistant", "content": "Nice to meet you, Riya. We can learn Python step by step."}, {"role": "user", "content": "What am I learning?"}], "must_contain_any": ["python"]},
]


def run_case(engine: LocalLLMEngine, case: dict[str, Any], max_new_tokens: int) -> dict[str, Any]:
    start = time.perf_counter()
    error = None
    answer = ""
    try:
        answer = engine.chat(case["messages"], max_new_tokens=max_new_tokens)
    except Exception as exc:  # keep evaluating the remaining cases
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start
    lowered = answer.casefold()
    required = [str(x).casefold() for x in case.get("must_contain", [])]
    any_required = [str(x).casefold() for x in case.get("must_contain_any", [])]
    checks = {
        "non_empty": bool(answer.strip()),
        "not_degenerate": bool(answer.strip()) and not is_degenerate_generation(answer),
        "required_terms": all(term in lowered for term in required),
        "one_of_required_terms": not any_required or any(term in lowered for term in any_required),
    }
    return {
        "id": case["id"],
        "answer": answer,
        "seconds": round(elapsed, 3),
        "error": error,
        "checks": checks,
        "passed_basic_checks": error is None and all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--output", default="artifacts/evaluations/native-chat-report.json")
    parser.add_argument("--cases", default=None, help="Optional JSON file containing a list of cases.")
    args = parser.parse_args()

    for label, value in (("config", args.config), ("tokenizer", args.tokenizer), ("checkpoint", args.checkpoint)):
        if not Path(value).is_file():
            parser.error(f"{label} file does not exist: {value}")
    if args.max_new_tokens < 1 or args.max_new_tokens > 2048:
        parser.error("--max-new-tokens must be between 1 and 2048")

    cases = DEFAULT_CASES
    if args.cases:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        if not isinstance(cases, list) or not cases:
            parser.error("--cases must contain a non-empty JSON array")

    engine = LocalLLMEngine()
    loaded = engine.load(args.config, args.tokenizer, args.checkpoint, device=args.device)
    results = [run_case(engine, case, args.max_new_tokens) for case in cases]
    passed = sum(item["passed_basic_checks"] for item in results)
    report = {
        "kind": "om_native_chat_evaluation",
        "semantic_correctness_certified": False,
        "note": "Passing structural checks is not proof of factual correctness. Review answers and use domain-specific tests.",
        "model": {
            "checkpoint": loaded.get("checkpoint"),
            "config": args.config,
            "tokenizer": loaded.get("tokenizer"),
            "tokenizer_fingerprint": loaded.get("tokenizer_fingerprint"),
            "device": loaded.get("device"),
            "parameters": loaded.get("parameters"),
        },
        "summary": {
            "cases": len(results),
            "basic_passed": passed,
            "basic_failed": len(results) - passed,
            "pass_rate": round(passed / len(results), 4),
        },
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": report["summary"], "semantic_correctness_certified": False}, indent=2))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
