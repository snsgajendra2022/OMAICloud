#!/usr/bin/env python3
"""Automatic real-teacher harvest → merge → OM SFT → OM-only (remove teachers)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "artifacts" / "auto_teach_train_run.out"


def log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def ensure_env() -> None:
    os.chdir(ROOT)
    os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")
    os.environ["OM_TEACHER_MODELS"] = os.environ.get("OM_TEACHER_MODELS", "mistral:latest")
    os.environ["OM_DISTILL_ALLOW_MOCK"] = "0"
    os.environ["OM_OLLAMA_BASE_URL"] = os.environ.get("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    os.environ["OM_OLLAMA_NUM_CTX"] = os.environ.get("OM_OLLAMA_NUM_CTX", "2048")
    os.environ["OM_OLLAMA_NUM_PREDICT"] = os.environ.get("OM_OLLAMA_NUM_PREDICT", "400")
    os.environ["OM_TEACHER_TIMEOUT"] = os.environ.get("OM_TEACHER_TIMEOUT", "600")
    os.environ["OM_TEACHER_PARALLELISM"] = "1"


def patch_env_file(**kv: str) -> None:
    env_path = ROOT / ".env"
    text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    lines = text.splitlines()
    keys = set(kv)
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        replaced = False
        for k, v in kv.items():
            if line.startswith(f"{k}="):
                out.append(f"{k}={v}")
                seen.add(k)
                replaced = True
                break
        if not replaced:
            out.append(line)
    for k in keys - seen:
        out.append(f"{k}={kv[k]}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def ensure_ollama() -> None:
    import urllib.request

    url = os.environ["OM_OLLAMA_BASE_URL"].rstrip("/") + "/"
    try:
        urllib.request.urlopen(url, timeout=3)
        return
    except Exception:
        subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                urllib.request.urlopen(url, timeout=2)
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("Ollama is not reachable on 127.0.0.1:11434")


def harvest() -> dict:
    from om_ai.core.distillation import CurriculumGenerator, create_teacher_manager

    topics = [
        ("software engineering fundamentals", "software"),
        ("React architecture", "software"),
        ("HTTP APIs and REST", "software"),
        ("databases SQL and indexes", "software"),
        ("distributed systems basics", "software"),
        ("security hardening for web apps", "security"),
        ("testing and observability", "software"),
        ("Kubernetes and containers", "devops"),
    ]
    manager = create_teacher_manager()
    manager.parallelism = 1
    gen = CurriculumGenerator()
    stats = {"questions": 0, "live_ok": 0, "exported": 0, "failed": 0}
    for topic, domain in topics:
        pack = gen.generate(topic, domain=domain, count=5)
        qs = [q["question"] for q in (pack.get("questions") or []) if q.get("question")]
        if not qs:
            qs = [f"Explain {topic} with practical steps and failure modes."]
        log(json.dumps({"topic": topic, "n": len(qs)}))
        for q in qs:
            stats["questions"] += 1
            try:
                result = manager.collect_and_save(q)
                h = result.get("harvest") or {}
                live = int(h.get("live_count") or 0)
                if live > 0:
                    stats["live_ok"] += 1
                else:
                    stats["failed"] += 1
                exported = int(((result.get("export") or {}).get("exported") or 0))
                stats["exported"] += exported
                log(json.dumps({"q": q[:90], "live": live, "exported": exported}))
            except Exception as exc:
                stats["failed"] += 1
                log(json.dumps({"q": q[:90], "error": str(exc)}))
    log(json.dumps({"harvest_stats": stats}))
    if stats["live_ok"] <= 0:
        raise RuntimeError("No live teacher answers collected")
    return stats


def merge_and_train() -> None:
    # Free GPU memory held by Ollama teachers before SFT.
    try:
        subprocess.call(
            [
                "curl",
                "-s",
                os.environ.get("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434") + "/api/generate",
                "-d",
                '{"model":"'
                + os.environ.get("OM_TEACHER_MODELS", "mistral:latest").split(",")[0]
                + '","keep_alive":0,"prompt":""}',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.call(["pkill", "-f", "llama-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    except Exception as exc:
        log(f"warn unload teachers: {exc}")

    py = str(ROOT / ".venv" / "bin" / "python")
    om = str(ROOT / ".venv" / "bin" / "om-ai")
    subprocess.check_call([py, str(ROOT / "scripts" / "merge_all_sft.py")])
    merged = ROOT / "data" / "training" / "om_all_sft_merged.jsonl"
    rows = sum(1 for _ in merged.open(encoding="utf-8") if _.strip())
    log(f"merged_rows={rows}")
    init = ROOT / "artifacts" / "checkpoints" / "om-1.0-chat-sft-v4" / "latest.pt"
    distill = ROOT / "artifacts" / "checkpoints" / "om-1.0-distill-sft" / "latest.pt"
    # Prefer clean chat init to avoid NaN-corrupted intermediate weights.
    if not init.exists() and distill.exists():
        init = distill
    steps = os.environ.get("OM_AUTO_SFT_STEPS", "400")
    device = os.environ.get("OM_MODEL_DEVICE", "mps")
    cmd = [
        om,
        "sft",
        "--config",
        "configs/om-1.0-local.json",
        "--data",
        "data/training/om_all_sft_merged.jsonl",
        "--tokenizer",
        "artifacts/tokenizer-production-65536.json",
        "--checkpoint",
        str(init),
        "--output",
        "artifacts/checkpoints/om-1.0-distill-sft",
        "--steps",
        str(steps),
        "--batch-size",
        "1",
        "--grad-accum",
        "2",
        "--lr",
        "1e-5",
        "--checkpoint-every",
        "100",
        "--device",
        device,
        "--precision",
        "fp32",
    ]
    log("SFT_CMD " + " ".join(cmd))
    subprocess.check_call(cmd)


def switch_to_om_only() -> None:
    patch_env_file(
        OM_MODEL_CHECKPOINT="artifacts/checkpoints/om-1.0-distill-sft/latest.pt",
        OM_MODEL_PROVIDER="om_native",
        OM_AI_CHAT_BACKEND="om_native",
        OM_DISTILL_ALLOW_MOCK="0",
        OM_TEACHER_MODELS=os.environ.get("OM_TEACHER_MODELS", "mistral:latest"),
    )
    if os.environ.get("OM_KEEP_TEACHERS", "0") == "1":
        log("OM_KEEP_TEACHERS=1 — keeping Ollama teachers")
        return
    # Teachers were only for data collection.
    try:
        listed = subprocess.check_output(["ollama", "list"], text=True)
    except Exception as exc:
        log(f"ollama list failed: {exc}")
        return
    for line in listed.splitlines()[1:]:
        name = (line.split() or [""])[0]
        if not name:
            continue
        log(f"ollama rm {name}")
        subprocess.call(["ollama", "rm", name])


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    # Append-only lock file so concurrent launches don't clobber progress.
    lock = ROOT / "artifacts" / "auto_harvest_train.lock"
    if lock.exists():
        try:
            old = int(lock.read_text().strip() or "0")
            os.kill(old, 0)
            log(f"Already running pid={old}; exit")
            return 0
        except Exception:
            pass
    lock.write_text(str(os.getpid()), encoding="utf-8")
    try:
        log(f"===== AUTO TEACH+TRAIN START {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} =====")
        ensure_env()
        patch_env_file(
            OM_TEACHER_MODELS=os.environ["OM_TEACHER_MODELS"],
            OM_DISTILL_ALLOW_MOCK="0",
            OM_OLLAMA_NUM_CTX=os.environ["OM_OLLAMA_NUM_CTX"],
            OM_OLLAMA_NUM_PREDICT=os.environ["OM_OLLAMA_NUM_PREDICT"],
        )
        ensure_ollama()
        stats = harvest()
        merge_and_train()
        switch_to_om_only()
        log("===== COMPLETE =====")
        log(
            json.dumps(
                {
                    "ok": True,
                    "harvest": stats,
                    "checkpoint": "artifacts/checkpoints/om-1.0-distill-sft/latest.pt",
                }
            )
        )
        return 0
    finally:
        try:
            if lock.exists() and lock.read_text().strip() == str(os.getpid()):
                lock.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"FATAL: {exc}")
        raise
