#!/usr/bin/env python3
"""Make the local .env select only OM's native model without exposing secrets.

This intentionally preserves OM checkpoint/config/tokenizer paths and unrelated
application settings. It removes third-party provider variables and overwrites
backend selectors that could route chat to vLLM/Qwen/OpenAI/Transformers.
"""
from __future__ import annotations

import argparse
from pathlib import Path

NATIVE_VALUES = {
    "OM_NATIVE_ONLY": "1",
    "OM_MODEL_PROVIDER": "om_native",
    "OM_AI_CHAT_BACKEND": "om_native",
    "OM_NATIVE_MODEL_FIRST": "1",
}
REMOVE_PREFIXES = ("OM_VLLM_", "OM_HF_", "OM_AI_OPENAI_")
REMOVE_KEYS = {"OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Set .env to native OM-only mode")
    parser.add_argument("--env", default=".env", help="Environment file to update (default: .env)")
    args = parser.parse_args()
    path = Path(args.env)
    if not path.exists():
        raise SystemExit(f"{path} does not exist. Create it first; this script will not invent model paths.")

    lines = path.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            output.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in REMOVE_KEYS or key.startswith(REMOVE_PREFIXES):
            continue
        if key in NATIVE_VALUES:
            if key not in seen:
                output.append(f"{key}={NATIVE_VALUES[key]}")
                seen.add(key)
            continue
        output.append(line)

    for key, value in NATIVE_VALUES.items():
        if key not in seen:
            output.append(f"{key}={value}")
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    print(f"Updated {path}: native OM-only backend enabled.")
    print("Preserved OM model config/checkpoint/tokenizer paths and unrelated settings.")
    print("Removed vLLM, Hugging Face, and OpenAI provider environment variables.")


if __name__ == "__main__":
    main()
