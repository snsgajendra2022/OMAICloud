#!/usr/bin/env python3
"""Run OM's evidence-based certification checks without inventing pass statuses."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "om_capability_registry.json"
REPORT = ROOT / "artifacts" / "certification" / "om_certification_report.json"


def run_check(name: str, command: list[str], *, timeout: int = 1800) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
            env={**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        output = proc.stdout[-20000:]
        return {
            "name": name, "command": command, "status": "PASS" if proc.returncode == 0 else "FAIL",
            "return_code": proc.returncode, "duration_seconds": round(time.perf_counter() - started, 3),
            "output_tail": output,
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        return {
            "name": name, "command": command, "status": "TIMEOUT", "return_code": None,
            "duration_seconds": round(time.perf_counter() - started, 3), "output_tail": str(out)[-20000:],
        }
    except OSError as exc:
        return {
            "name": name, "command": command, "status": "ERROR", "return_code": None,
            "duration_seconds": round(time.perf_counter() - started, 3), "output_tail": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-tests", action="store_true", help="Run the complete pytest suite.")
    parser.add_argument("--run-model-eval", action="store_true", help="Run native capability evaluation (requires local model artifacts).")
    parser.add_argument("--output", type=Path, default=REPORT, help="JSON report path.")
    args = parser.parse_args()

    if not REGISTRY.is_file():
        print(f"ERROR: capability registry missing: {REGISTRY}", file=sys.stderr)
        return 2
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks = [
        run_check("compileall", [sys.executable, "-m", "compileall", "-q", "om_ai", "scripts"]),
        run_check("architecture_audit", [sys.executable, "scripts/audit_om_architecture.py"]),
    ]
    if args.run_tests:
        checks.append(run_check("pytest", [sys.executable, "-m", "pytest", "-q"], timeout=3600))
    if args.run_model_eval:
        eval_script = ROOT / "scripts" / "evaluate_om_capabilities.py"
        if eval_script.is_file():
            checks.append(run_check("native_model_evaluation", [sys.executable, str(eval_script)], timeout=7200))
        else:
            checks.append({"name": "native_model_evaluation", "status": "NOT_RUN", "reason": "evaluation script not found"})

    missing_files = []
    for capability in registry.get("capabilities", []):
        impl = capability.get("implementation") or {}
        for relative in impl.get("files") or []:
            candidate = ROOT / relative
            if not candidate.exists():
                missing_files.append({"capability": capability.get("id"), "path": relative})

    completed_checks = [item for item in checks if item.get("status") == "PASS"]
    failed_checks = [item for item in checks if item.get("status") in {"FAIL", "ERROR", "TIMEOUT"}]
    report = {
        "schema_version": 1,
        "project": "OM AI",
        "created_at_unix": time.time(),
        "branch_note": "Run this script from the checkout/branch you intend to certify.",
        "registry_path": str(REGISTRY.relative_to(ROOT)),
        "capability_count": len(registry.get("capabilities", [])),
        "capability_status_counts": {
            status: sum(1 for c in registry.get("capabilities", []) if c.get("status") == status)
            for status in sorted({str(c.get("status", "UNSPECIFIED")) for c in registry.get("capabilities", [])})
        },
        "checks": checks,
        "missing_implementation_paths": missing_files,
        "summary": {
            "checks_passed": len(completed_checks),
            "checks_failed": len(failed_checks),
            "missing_implementation_paths": len(missing_files),
            "production_certified": False,
            "reason": "Certification remains false until model/tokenizer compatibility, real generation quality, integration, security, and capability-specific tests pass.",
        },
        "limitations": [
            "Static compile and architecture checks do not prove runtime reachability or answer quality.",
            "Model evaluation must run against the intended local checkpoint and tokenizer; ignored local artifacts are not uploaded or inferred.",
            "This report never upgrades a capability to CERTIFIED solely because source files exist.",
        ],
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(output),
        "capabilities": report["capability_count"],
        "checks_passed": len(completed_checks),
        "checks_failed": len(failed_checks),
        "missing_implementation_paths": len(missing_files),
        "production_certified": False,
    }, indent=2))
    for check in checks:
        print(f"{check['status']:>8}  {check['name']}")
        if check.get("status") in {"FAIL", "ERROR", "TIMEOUT"}:
            detail = check.get("output_tail") or check.get("reason") or "No diagnostic output captured."
            print(f"\n--- {check['name']} diagnostic (last 20,000 chars) ---")
            print(detail.rstrip())
            print(f"--- end {check['name']} diagnostic ---\n")
            if check.get("name") == "native_model_evaluation":
                eval_report = ROOT / "artifacts" / "evaluations" / "om-capability-smoke.json"
                if eval_report.is_file():
                    try:
                        evaluation = json.loads(eval_report.read_text(encoding="utf-8"))
                        print("--- Failed native model cases ---")
                        for item in evaluation.get("results", []):
                            if item.get("ok"):
                                continue
                            print(f"\n[{item.get('category', 'unknown')}]")
                            print("Prompt:", item.get("prompt", ""))
                            print("Answer:", item.get("answer", item.get("error", "<no answer>")))
                            if item.get("correctness_checks") is not None:
                                print("Checks:", json.dumps(item["correctness_checks"], ensure_ascii=False))
                        print("--- end failed native model cases ---\n")
                    except (OSError, json.JSONDecodeError) as exc:
                        print(f"Could not read evaluation details: {exc}")

    if missing_files:
        print("\n--- Missing implementation paths ---")
        for item in missing_files:
            print(f"  - {item.get('capability', '<unknown capability>')}: {item.get('path')}")
        print("--- end missing implementation paths ---")

    print("\nCertification is evidence-based: a failed native model evaluation cannot be overridden by this script.")
    return 1 if failed_checks or missing_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
