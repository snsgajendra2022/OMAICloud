#!/usr/bin/env python3
"""Audit a chat SFT JSONL before spending time on another training run."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.training.sft import _row_to_messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--max-seq-len", type=int, required=True)
    parser.add_argument("--output", default="artifacts/evaluations/sft-data-audit.json")
    args = parser.parse_args()

    data_path = Path(args.data)
    tokenizer_path = Path(args.tokenizer)
    if not data_path.is_file():
        parser.error(f"data file does not exist: {data_path}")
    if not tokenizer_path.is_file():
        parser.error(f"tokenizer file does not exist: {tokenizer_path}")
    if args.max_seq_len < 8:
        parser.error("--max-seq-len must be at least 8")

    tokenizer = load_tokenizer(tokenizer_path)
    if not tokenizer.inspect().get("chat_tokens_available"):
        parser.error("SFT audit requires a tokenizer with chat special tokens")

    counts = Counter()
    seen_rows: set[str] = set()
    seen_prompts: set[str] = set()
    seen_responses: set[str] = set()
    prompt_lengths: list[int] = []
    response_lengths: list[int] = []
    supervised_lengths: list[int] = []
    examples: list[dict] = []

    with data_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                counts["blank_lines"] += 1
                continue
            counts["rows"] += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                counts["invalid_json"] += 1
                continue
            if not isinstance(obj, dict):
                counts["non_object_rows"] += 1
                continue
            messages, response = _row_to_messages(obj)
            if not messages or not response:
                counts["missing_prompt_or_response"] += 1
                continue
            counts["valid_rows"] += 1

            prompt_text = "\n".join(f"{m['role']}:{m['content']}" for m in messages)
            prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
            response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()
            pair_hash = hashlib.sha256((prompt_hash + response_hash).encode()).hexdigest()
            if pair_hash in seen_rows:
                counts["duplicate_pairs"] += 1
            seen_rows.add(pair_hash)
            if prompt_hash in seen_prompts:
                counts["repeated_prompts"] += 1
            seen_prompts.add(prompt_hash)
            if response_hash in seen_responses:
                counts["repeated_responses"] += 1
            seen_responses.add(response_hash)

            try:
                prefix_ids = tokenizer.encode_chat(messages, add_generation_prompt=True, add_eos=False)
                response_ids = tokenizer.encode(response)
            except Exception:
                counts["tokenization_errors"] += 1
                continue

            stop_ids = []
            if tokenizer.assistant_end_id is not None:
                stop_ids.append(tokenizer.assistant_end_id)
            stop_ids.append(tokenizer.eos_id)
            full_target_len = len(response_ids) + len(stop_ids)
            target_budget = min(full_target_len, max(2, args.max_seq_len // 2))
            supervised_len = min(len(response_ids), max(0, target_budget - len(stop_ids))) + len(stop_ids)
            if full_target_len > target_budget:
                counts["response_truncated"] += 1
            prefix_budget = args.max_seq_len - supervised_len
            if prefix_budget <= 0:
                counts["no_prompt_budget"] += 1
                continue
            if len(prefix_ids) > prefix_budget:
                counts["prompt_truncated"] += 1
            prompt_lengths.append(len(prefix_ids))
            response_lengths.append(len(response_ids))
            supervised_lengths.append(supervised_len)

            if len(examples) < 8:
                examples.append({
                    "line": line_number,
                    "prompt_tokens_before_truncation": len(prefix_ids),
                    "response_tokens_before_truncation": len(response_ids),
                    "supervised_tokens_after_truncation": supervised_len,
                    "will_truncate_prompt": len(prefix_ids) > prefix_budget,
                    "will_truncate_response": full_target_len > target_budget,
                })

    total = counts["rows"]
    valid = counts["valid_rows"]
    unique_responses = len(seen_responses)
    repeated_response_rate = counts["repeated_responses"] / valid if valid else 0.0
    response_diversity_rate = unique_responses / valid if valid else 0.0
    warnings = []
    if valid >= 100 and repeated_response_rate >= 0.5 and response_diversity_rate < 0.25:
        warnings.append(
            "low_response_diversity: many rows share response text; review the dataset "
            "for templated or generic targets before retraining."
        )
    if valid and counts["duplicate_pairs"] / valid >= 0.1:
        warnings.append("high_duplicate_pair_rate: remove exact duplicate prompt/response pairs.")
    report = {
        "kind": "om_sft_dataset_audit",
        "data": str(data_path),
        "tokenizer": str(tokenizer_path),
        "tokenizer_fingerprint": tokenizer_fingerprint(tokenizer_path),
        "max_seq_len": args.max_seq_len,
        "summary": dict(counts),
        "rates": {
            "valid_row_rate": round(valid / total, 4) if total else 0.0,
            "duplicate_pair_rate_of_valid": round(counts["duplicate_pairs"] / valid, 4) if valid else 0.0,
            "prompt_truncation_rate": round(counts["prompt_truncated"] / valid, 4) if valid else 0.0,
            "response_truncation_rate": round(counts["response_truncated"] / valid, 4) if valid else 0.0,
        },
        "token_lengths": {
            "prompt_max": max(prompt_lengths, default=0),
            "response_max": max(response_lengths, default=0),
            "supervised_tokens_min": min(supervised_lengths, default=0),
            "supervised_tokens_median": sorted(supervised_lengths)[len(supervised_lengths) // 2] if supervised_lengths else 0,
        },
        "sampled_rows": examples,
        "limitations": [
            "This is a data-shape and truncation audit, not a semantic quality review.",
            "Duplicate responses can be legitimate; inspect rates and examples before filtering.",
            "No model weights are changed and no training is started.",
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": report["summary"], "rates": report["rates"], "warnings": warnings}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
