#!/usr/bin/env python3
"""Estimate LLM weight memory before allocating hardware.

This is a planning estimate, not a benchmark. KV-cache estimates use a configurable
architecture approximation and should be replaced with model config values when known.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def estimate(
    parameters: int,
    *,
    precision: str = "fp16",
    context: int = 4096,
    concurrent_sequences: int = 1,
    layers: int = 80,
    kv_heads: int = 8,
    head_dim: int = 128,
    kv_bytes: int = 2,
    overhead_ratio: float = 0.20,
) -> dict:
    if parameters <= 0 or context <= 0 or concurrent_sequences <= 0:
        raise ValueError("parameters, context, and concurrent_sequences must be positive")
    bytes_per_parameter = {"fp32": 4, "fp16": 2, "bf16": 2, "int8": 1, "int4": 0.5}
    if precision not in bytes_per_parameter:
        raise ValueError(f"Unsupported precision: {precision}")
    weight_bytes = parameters * bytes_per_parameter[precision]
    # KV cache = K and V * layers * tokens * concurrent sequences * KV width * bytes.
    kv_cache_bytes = 2 * layers * context * concurrent_sequences * kv_heads * head_dim * kv_bytes
    quantization_overhead = weight_bytes * (0.05 if precision == "int4" else 0.02 if precision == "int8" else 0)
    estimated_total = (weight_bytes + quantization_overhead + kv_cache_bytes) * (1 + overhead_ratio)
    gib = 1024**3
    return {
        "parameters": parameters,
        "precision": precision,
        "context_tokens": context,
        "concurrent_sequences": concurrent_sequences,
        "raw_weight_gib": round(weight_bytes / gib, 2),
        "estimated_kv_cache_gib": round(kv_cache_bytes / gib, 2),
        "runtime_overhead_ratio": overhead_ratio,
        "estimated_total_gib": round(estimated_total / gib, 2),
        "warning": "Planning estimate only; actual memory depends on architecture, quantizer, kernels, batching, and runtime.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=int, default=70_000_000_000)
    parser.add_argument("--precision", choices=["fp32", "fp16", "bf16", "int8", "int4"], default="int4")
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--layers", type=int, default=80)
    parser.add_argument("--kv-heads", type=int, default=8)
    parser.add_argument("--head-dim", type=int, default=128)
    parser.add_argument("--kv-bytes", type=int, choices=[1, 2, 4], default=2)
    parser.add_argument("--overhead-ratio", type=float, default=0.20)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.overhead_ratio < 0 or args.overhead_ratio > 5:
        parser.error("--overhead-ratio must be between 0 and 5")
    report = estimate(
        args.parameters, precision=args.precision, context=args.context,
        concurrent_sequences=args.concurrency, layers=args.layers,
        kv_heads=args.kv_heads, head_dim=args.head_dim, kv_bytes=args.kv_bytes,
        overhead_ratio=args.overhead_ratio,
    )
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
