#!/usr/bin/env python3
"""Run OM's native checkpoint against the required 13-case capability suite.

This is an evaluation harness, not a model-quality fix or a standardized benchmark.
It never invokes a hosted provider. Deterministic checks are necessary checks only;
subjective semantic correctness remains explicitly marked for human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from om_ai.backends.om_native import OMNativeBackend, default_native_paths
from om_ai.runtime.engine import is_degenerate_generation
from om_ai.runtime.chat_orchestrator import is_low_quality_reply

CASES = [
    {"id": "01_greeting_hi", "category": "greeting", "prompt": "Hi.", "messages": [{"role": "user", "content": "Hi."}], "checks": "greeting"},
    {"id": "02_greeting_how_are_you", "category": "greeting", "prompt": "How are you?", "messages": [{"role": "user", "content": "How are you?"}], "checks": "greeting"},
    {"id": "03_introduction", "category": "introduction", "prompt": "Introduce yourself in one sentence.", "messages": [{"role": "user", "content": "Introduce yourself in one sentence."}], "checks": "introduction"},
    {"id": "04_capabilities", "category": "identity", "prompt": "What can you help me with?", "messages": [{"role": "user", "content": "What can you help me with?"}], "checks": "capabilities"},
    {"id": "05_ai_explanation", "category": "explanation", "prompt": "What is artificial intelligence?", "messages": [{"role": "user", "content": "What is artificial intelligence?"}], "checks": "ai"},
    {"id": "06_api_definition", "category": "definition", "prompt": "Explain what an API is.", "messages": [{"role": "user", "content": "Explain what an API is."}], "checks": "api"},
    {"id": "07_english_tips", "category": "instruction", "prompt": "Give me three tips for learning English.", "messages": [{"role": "user", "content": "Give me three tips for learning English."}], "checks": "three_tips"},
    {"id": "08_summarization", "category": "summarization", "prompt": "Summarize this paragraph in one sentence: Bees pollinate many flowering plants. This helps plants produce fruits and seeds. Healthy pollinator populations support food production and ecosystems.", "messages": [{"role": "user", "content": "Summarize this paragraph in one sentence: Bees pollinate many flowering plants. This helps plants produce fruits and seeds. Healthy pollinator populations support food production and ecosystems."}], "checks": "summary"},
    {"id": "09_extraction", "category": "extraction", "prompt": "Extract the facts exactly: Name: Mira; City: Pune; Favorite language: Python. Return the name, city, and favorite language.", "messages": [{"role": "user", "content": "Extract the facts exactly: Name: Mira; City: Pune; Favorite language: Python. Return the name, city, and favorite language."}], "checks": "extraction"},
    {"id": "10_logic", "category": "reasoning", "prompt": "All zargs are wugs. Some wugs are red. Can we conclude that some zargs are red? Explain briefly.", "messages": [{"role": "user", "content": "All zargs are wugs. Some wugs are red. Can we conclude that some zargs are red? Explain briefly."}], "checks": "logic"},
    {"id": "11_code_explanation", "category": "coding", "prompt": "Explain this Python code: def add(a, b):\n    return a + b", "messages": [{"role": "user", "content": "Explain this Python code: def add(a, b):\n    return a + b"}], "checks": "code"},
    {"id": "12_context_retention", "category": "context retention", "prompt": "Earlier in this conversation, the user said their project codename is MAPLE-731. What is the project codename? Reply with the code only.", "messages": [{"role": "user", "content": "My project codename is MAPLE-731. Remember it for the next question."}, {"role": "assistant", "content": "I will use that information for the next question."}, {"role": "user", "content": "What is my project codename? Reply with the code only."}], "checks": "context"},
    {"id": "13_unknown_information", "category": "uncertainty", "prompt": "What is the exact temperature inside my room right now? No sensor reading or location has been provided.", "messages": [{"role": "user", "content": "What is the exact temperature inside my room right now? No sensor reading or location has been provided."}], "checks": "uncertainty"},
]

def deterministic_checks(kind: str, answer: str) -> dict[str, bool]:
    text = (answer or "").strip()
    low = text.lower()
    checks: dict[str, bool] = {}
    if kind == "greeting":
        checks["contains_greeting_or_response"] = bool(re.search(r"\b(hi|hello|hey|well|good|doing|help|thanks|thank)\b", low))
    elif kind == "introduction":
        checks["mentions_om_or_ai"] = "om" in low or "ai" in low
        checks["sentence_like"] = len(re.findall(r"[.!?](?:['\"”)]*)?(?:\s|$)", text)) <= 2
    elif kind == "capabilities":
        checks["mentions_at_least_one_capability"] = any(w in low for w in ("help", "answer", "explain", "write", "code", "learn", "question", "task"))
    elif kind == "ai":
        checks["describes_intelligence_or_computers"] = any(w in low for w in ("computer", "machine", "system", "software", "intelligence", "task", "data", "learn"))
    elif kind == "api":
        checks["describes_interface_or_communication"] = any(w in low for w in ("interface", "application", "software", "communicat", "request", "response", "service", "system"))
    elif kind == "three_tips":
        checks["three_list_items"] = len(re.findall(r"(?m)^\s*(?:\d+[.)]|[-*])\s+\S", text)) == 3
        checks["english_learning_relevant"] = any(w in low for w in ("speak", "listen", "read", "write", "practice", "vocabulary", "english"))
    elif kind == "summary":
        checks["mentions_bees_or_pollination"] = any(w in low for w in ("bee", "pollinat"))
        checks["mentions_plants_or_food_or_ecosystem"] = any(w in low for w in ("plant", "fruit", "seed", "food", "ecosystem"))
    elif kind == "extraction":
        checks["extracts_name"] = bool(re.search(r"\bmira\b", low))
        checks["extracts_city"] = bool(re.search(r"\bpune\b", low))
        checks["extracts_language"] = "python" in low
    elif kind == "logic":
        checks["does_not_infer_some_zargs_are_red"] = any(p in low for p in ("cannot conclude", "can't conclude", "not necessarily", "does not follow", "doesn't follow", "not enough information", "no conclusion"))
    elif kind == "code":
        checks["explains_addition_or_return_value"] = any(w in low for w in ("add", "sum", "addition", "return", "plus", "result"))
    elif kind == "context":
        checks["recalls_exact_code"] = "MAPLE-731" in text.upper()
    elif kind == "uncertainty":
        checks["acknowledges_missing_measurement_or_access"] = any(p in low for p in ("cannot know", "can't know", "cannot tell", "can't tell", "don't have", "do not have", "no sensor", "need a sensor", "not provided", "unable to measure", "can't measure", "cannot measure", "not access"))
    return checks

def file_identity(path: str) -> dict:
    p = Path(path)
    item = {"path": str(p.resolve(strict=False)), "exists": p.is_file()}
    if p.is_file():
        item["size_bytes"] = p.stat().st_size
        digest = hashlib.sha256()
        with p.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        item["sha256"] = digest.hexdigest()
    return item

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/evaluations/om-native-13-case.json")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--config")
    parser.add_argument("--tokenizer")
    parser.add_argument("--checkpoint")
    parser.add_argument("--device")
    args = parser.parse_args()
    if args.max_new_tokens < 1:
        parser.error("--max-new-tokens must be greater than zero")

    paths = default_native_paths()
    for key, value in (("config", args.config), ("tokenizer", args.tokenizer), ("checkpoint", args.checkpoint)):
        if value:
            paths[key] = str(Path(value).expanduser().resolve(strict=False))
    if args.device:
        paths["device"] = args.device
    required = ("config", "tokenizer", "checkpoint")
    missing = [{"asset": key, "path": paths.get(key)} for key in required if not paths.get(key) or not Path(paths[key]).is_file()]
    if missing:
        report = {"ok": False, "stage": "preflight", "backend": "om_native", "missing": missing, "case_count": len(CASES), "hint": "Provide matching local config, tokenizer and checkpoint artifacts. No hosted fallback is attempted."}
        print(json.dumps(report, indent=2))
        return 2

    backend = OMNativeBackend()
    try:
        load_info = backend.load(config_path=paths["config"], tokenizer_path=paths["tokenizer"], checkpoint_path=paths["checkpoint"], device=paths.get("device") or None, require_checkpoint=True)
    except Exception as exc:
        report = {"ok": False, "stage": "load", "backend": "om_native", "error_type": type(exc).__name__, "error": str(exc), "case_count": len(CASES), "hosted_fallback_used": False}
        print(json.dumps(report, indent=2))
        return 2

    results = []
    for case in CASES:
        started = time.perf_counter()
        try:
            answer = backend.chat(case["messages"], max_new_tokens=args.max_new_tokens, temperature=0.2, top_p=0.9, top_k=40, repetition_penalty=1.1, min_new_tokens=1)
            answer = answer or ""
            elapsed = round(time.perf_counter() - started, 3)
            checks = deterministic_checks(case["checks"], answer)
            withheld = "could not produce a reliable answer" in answer.lower() and "failed quality checks" in answer.lower()
            usable = bool(answer.strip()) and not withheld and not is_degenerate_generation(answer) and not bool(is_low_quality_reply(answer))
            checks_pass = bool(checks) and all(checks.values())
            results.append({**{k: case[k] for k in ("id", "category", "prompt")}, "ok": usable and checks_pass, "usable_output": usable, "quality_gate_withheld": withheld, "deterministic_checks": checks, "semantic_review": "required", "raw_answer_available": False, "final_answer": answer[:4000], "elapsed_seconds": elapsed, "fallback_used": False, "hosted_model_used": False, "failure_reason": None if usable and checks_pass else ("unusable_or_withheld_output" if not usable else "deterministic_check_failed")})
        except Exception as exc:
            results.append({**{k: case[k] for k in ("id", "category", "prompt")}, "ok": False, "usable_output": False, "semantic_review": "required", "raw_answer_available": False, "final_answer": None, "fallback_used": False, "hosted_model_used": False, "failure_reason": "generation_exception", "error_type": type(exc).__name__, "error": str(exc)[:1000], "elapsed_seconds": round(time.perf_counter() - started, 3)})

    passed = sum(bool(item.get("ok")) for item in results)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "suite": "OM native 13-case capability suite",
        "backend": "om_native",
        "hosted_fallback_used": False,
        "fallbacks_count_as_pass": False,
        "case_count": len(results),
        "passed_case_count": passed,
        "failed_case_count": len(results) - passed,
        "semantic_review_required": True,
        "release_ready": False,
        "release_readiness_note": "Passing deterministic checks alone does not establish semantic correctness. Human review and all repository release gates remain required.",
        "load": {"device": load_info.get("device"), "parameters": load_info.get("parameters"), "checkpoint": load_info.get("checkpoint") or load_info.get("checkpoint_path"), "tokenizer_fingerprint": load_info.get("tokenizer_fingerprint"), "config_file": file_identity(paths["config"]), "tokenizer_file": file_identity(paths["tokenizer"]), "checkpoint_file": file_identity(paths["checkpoint"])},
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(output), "case_count": len(results), "passed": passed, "failed": len(results)-passed, "release_ready": False, "hosted_fallback_used": False}, indent=2))
    return 0 if passed == len(CASES) else 1

if __name__ == "__main__":
    raise SystemExit(main())
