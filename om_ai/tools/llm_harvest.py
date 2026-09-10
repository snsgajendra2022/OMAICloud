#!/usr/bin/env python3
"""CLI helper: harvest teacher LLM answers into OM training JSONL.

Example:
  .venv/bin/python -m om_ai.tools.llm_harvest \\
      --task "Explain Kubernetes architecture" \\
      --out data/om_distillation/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="OM Multi-LLM Teacher Distillation (STEP 94)")
    p.add_argument("--task", required=True, help="Question / instruction to harvest")
    p.add_argument(
        "--teachers",
        default="gpt,claude,gemini,qwen",
        help="Comma-separated provider ids",
    )
    p.add_argument("--out", default="data/om_distillation/", help="Output directory")
    p.add_argument("--no-mock", action="store_true", help="Fail if a teacher key is missing")
    p.add_argument("--json", action="store_true", help="Print full JSON result")
    args = p.parse_args(argv)

    from om_ai.core.distillation import TeacherManager

    teachers = [t.strip() for t in str(args.teachers).split(",") if t.strip()]
    manager = TeacherManager(teachers=teachers, allow_mock=not args.no_mock)
    result = manager.collect_and_save(args.task, output=Path(args.out), teachers=teachers)

    if args.json:
        # Trim huge ranked texts for stdout unless needed
        print(json.dumps(result, indent=2, ensure_ascii=False)[:20000])
    else:
        ranking = result.get("ranking") or {}
        best = ranking.get("best") or {}
        export = result.get("export") or {}
        print("STEP 94 · Teacher Distillation")
        print(f"run_id:     {result.get('run_id')}")
        print(f"teachers:   {', '.join(teachers)}")
        print(f"best:       {best.get('provider')} score={best.get('score')}")
        print(f"common:     {', '.join((result.get('comparison') or {}).get('common_points') or [])}")
        print(f"exported:   {export.get('exported')}")
        for k, v in (export.get("written") or {}).items():
            print(f"  {k}: {v}")
    return 0 if result.get("saved") else 1


if __name__ == "__main__":
    sys.exit(main())
