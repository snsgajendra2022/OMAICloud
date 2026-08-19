#!/usr/bin/env python3
from pathlib import Path
import json, shutil, subprocess, sys

root = Path.cwd().resolve()
config = root / "configs/70b.json"
tokenizer = root / "artifacts/tokenizer-production-65536.json"
out = root / "artifacts/checkpoints/om-70b"

if not config.is_file() or not tokenizer.is_file():
    print("Run this from the OMAICloud repo root.")
    sys.exit(2)

candidates = [
    root / "data/production-corpus/clean/fineweb-1gb.jsonl",
    root / "data/production-corpus/raw/fineweb-1gb.txt",
    root / "data/production-corpus/clean/fineweb-deduped.jsonl",
    root / "data/production-corpus/raw/fineweb-100mb.txt",
]
corpora = [p for p in candidates if p.is_file()]
if not corpora:
    print("No local corpus found.")
    sys.exit(3)

corpus = max(corpora, key=lambda p: p.stat().st_size)
out.mkdir(parents=True, exist_ok=True)
free_gib = shutil.disk_usage(out).free / (1024**3)
dev_min_free = min(1.0, max(0.25, round(free_gib * 0.5, 2)))

try:
    import torch
    cuda = bool(torch.cuda.is_available())
    gpu_count = int(torch.cuda.device_count())
    mps = bool(torch.backends.mps.is_available())
except Exception:
    cuda = False
    gpu_count = 0
    mps = False

print("OM-70B MAC DEV PREFLIGHT")
print("Corpus:", corpus)
print("Free GiB:", round(free_gib, 2))
print("CUDA:", cuda, "GPU count:", gpu_count, "MPS:", mps)

cmd = [
    "om-ai","train-70b",
    "--config", str(config),
    "--data", str(corpus),
    "--tokenizer", str(tokenizer),
    "--output", str(out),
    "--strategy","deepspeed_zero3",
    "--preflight-only",
    "--allow-cpu",
    "--min-free-gb", str(dev_min_free),
    "--min-corpus-bytes","1000000",
]
print("Running:", " ".join(cmd))
rc = subprocess.run(cmd, cwd=root).returncode

report_path = out / "preflight_report.json"
if not report_path.is_file():
    print("No preflight report created.")
    sys.exit(rc or 4)

report = json.loads(report_path.read_text())
for c in report.get("checks", []):
    print(("PASS" if c.get("ok") else "FAIL"), c.get("name"), "-", c.get("detail"))

status = {
    "mac_dev_preflight_passed": bool(report.get("ok")),
    "real_70b_training_started": False,
    "real_70b_cuda_hardware_ready": bool(cuda and gpu_count >= 8),
    "cuda": cuda,
    "gpu_count": gpu_count,
    "mps": mps,
    "free_gib": round(free_gib, 2),
    "corpus": str(corpus),
    "note": "Mac dev preflight only. Real OM-70B training still requires a CUDA multi-GPU cluster and far more storage/data."
}
(root / "artifacts/checkpoints/om-70b/MAC_DEV_PREFLIGHT_STATUS.json").write_text(json.dumps(status, indent=2))

if not report.get("ok"):
    sys.exit(rc or 5)

print("DONE: Mac development preflight passed.")
print("Production CUDA safeguards remain unchanged.")
