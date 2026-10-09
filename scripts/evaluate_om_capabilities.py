#!/usr/bin/env python3
"""Run a reproducible smoke evaluation against OM's native backend only.

This produces a capability sample report, not a benchmark score or parity claim.
No hosted LLM or external inference service is called.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from om_ai.backends.om_native import OMNativeBackend, default_native_paths


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/evaluations/om-capability-smoke.json")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()

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
    conversation = []
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
            usable = bool((answer or "").strip())
            if not usable:
                failures += 1
            results.append({
                "category": category,
                "ok": usable,
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
                followup_ok = bool((followup or "").strip())
                if not followup_ok:
                    failures += 1
                results.append({
                    "category": "context_retention_followup",
                    "ok": followup_ok,
                    "elapsed_seconds": followup_elapsed,
                    "prompt": conversation[-1]["content"],
                    "answer": (followup or "")[:1000],
                    "expected_contains": "MAPLE-731",
                    "contains_expected": "MAPLE-731" in (followup or ""),
                })
        except Exception as exc:
            failures += 1
            results.append({
                "category": category,
                "ok": False,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "prompt": prompt,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

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
        "usable_output_count": sum(1 for item in results if item.get("ok")),
        "failed_output_count": failures,
        "note": "Smoke evaluation only. Read answers and score correctness manually or with a separately validated evaluator; this is not proof of cloud-model parity.",
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": failures == 0,
        "report": str(output),
        "case_count": len(results),
        "usable_output_count": report["usable_output_count"],
        "failed_output_count": failures,
        "hosted_fallback_used": False,
    }, indent=2))
    return 0 if failures == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
