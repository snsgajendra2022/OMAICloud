"""OM-70B training launcher: preflight → distributed pretrain → SFT → preference → gates.

This does **not** claim frontier / GPT-equivalent capability. Promotion to
``trained=True`` / production candidate requires measured benchmark gates.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from om_ai.training.preflight import run_preflight, write_report

Stage = Literal[
    "NOT_STARTED",
    "PREFLIGHT",
    "PRETRAIN",
    "PRETRAINED",
    "SFT",
    "ALIGNED",
    "BENCHMARKED",
    "PRODUCTION_CANDIDATE",
    "FAILED",
]


DEFAULT_GATES = {
    "min_benchmark_score": 0.0,  # set >0 when you own real eval suites
    "require_benchmark_file": True,
    "never_claim_frontier_without_metrics": True,
}


@dataclass
class Train70BStatus:
    stage: Stage = "NOT_STARTED"
    updated_at: str = ""
    config: str = "configs/70b.json"
    data: str = ""
    tokenizer: str = ""
    output: str = ""
    strategy: str = "deepspeed_zero3"
    messages: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    trained: bool = False
    production_candidate: bool = False

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def status_path(output: str | Path) -> Path:
    return Path(output) / "OM70B_TRAINING_STATUS.json"


def load_status(output: str | Path) -> Train70BStatus:
    path = status_path(output)
    if not path.is_file():
        return Train70BStatus(output=str(output))
    data = json.loads(path.read_text())
    return Train70BStatus(**{k: v for k, v in data.items() if k in Train70BStatus.__dataclass_fields__})


def save_status(st: Train70BStatus) -> Path:
    st.touch()
    path = status_path(st.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(st.to_dict(), indent=2))
    return path


def _log(st: Train70BStatus, msg: str) -> None:
    st.messages.append(f"{datetime.now(timezone.utc).isoformat()} {msg}")
    print(msg, flush=True)


def load_gates(path: str | Path | None) -> dict[str, Any]:
    gates = dict(DEFAULT_GATES)
    if path and Path(path).is_file():
        gates.update(json.loads(Path(path).read_text()))
    return gates


def _launch_deepspeed(
    *,
    config: str,
    data: str,
    tokenizer: str,
    deepspeed_config: str,
    output: str,
    num_gpus: int | None,
) -> int:
    import shutil

    script = str(Path(__file__).resolve().parent / "deepspeed_train.py")
    args = [
        script,
        "--config",
        config,
        "--data",
        data,
        "--tokenizer",
        tokenizer,
        "--deepspeed",
        deepspeed_config,
        "--output",
        output,
        "--partition-init",
    ]
    ds_bin = shutil.which("deepspeed")
    if ds_bin:
        cmd = [ds_bin]
        if num_gpus:
            cmd.append(f"--num_gpus={num_gpus}")
        cmd.extend(args)
    else:
        nproc = num_gpus or 1
        cmd = [
            sys.executable,
            "-m",
            "torch.distributed.run",
            f"--nproc_per_node={nproc}",
            *args,
        ]
    env = os.environ.copy()
    env["OM_AI_TRAIN_OUTPUT"] = output
    print("Launching:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, env=env)


def _launch_fsdp(
    *,
    config: str,
    data: str,
    tokenizer: str,
    output: str,
    steps: int,
    nproc: int,
) -> int:
    script = "om_ai.training.distributed"
    cmd = [
        sys.executable,
        "-m",
        "torch.distributed.run",
        f"--nproc_per_node={nproc}",
        "-m",
        script,
        "--config",
        config,
        "--data",
        data,
        "--tokenizer",
        tokenizer,
        "--strategy",
        "fsdp",
        "--steps",
        str(steps),
        "--output",
        output,
        "--partition-init",
    ]
    print("Launching:", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def run_train_70b(
    *,
    data: str,
    tokenizer: str,
    output: str,
    config: str = "configs/70b.json",
    deepspeed_config: str = "configs/deepspeed_zero3.json",
    strategy: str = "deepspeed_zero3",
    preflight_only: bool = False,
    resume: bool = False,
    sft_data: str | None = None,
    preference_data: str | None = None,
    benchmark: str | None = None,
    gates_path: str | None = None,
    min_gpus: int = 8,
    min_vram_gb: float = 40.0,
    min_free_gb: float = 500.0,
    min_corpus_bytes: int = 1_000_000,
    allow_cpu: bool = False,
    manifest: str | None = None,
    pretrain_steps: int = 1000,
    skip_posttrain: bool = False,
) -> Train70BStatus:
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    st = load_status(out) if resume else Train70BStatus()
    st.config = config
    st.data = data
    st.tokenizer = tokenizer
    st.output = str(out)
    st.strategy = strategy
    st.stage = "PREFLIGHT"
    st.trained = False
    st.production_candidate = False
    save_status(st)

    report = run_preflight(
        data=data,
        tokenizer=tokenizer,
        output=out,
        config=config,
        min_gpus=min_gpus,
        min_vram_gb=min_vram_gb,
        min_free_gb=min_free_gb,
        min_corpus_bytes=min_corpus_bytes,
        allow_cpu=allow_cpu,
        manifest=manifest,
    )
    report_path = write_report(report, out / "preflight_report.json")
    st.artifacts["preflight_report"] = str(report_path)
    _log(st, f"Preflight ok={report.ok} → {report_path}")
    save_status(st)

    if not report.ok:
        st.stage = "FAILED"
        _log(st, "Preflight failed — refusing to start 70B training.")
        save_status(st)
        return st

    if preflight_only:
        _log(st, "Preflight-only mode; not starting training.")
        save_status(st)
        return st

    # --- Pretrain ---
    st.stage = "PRETRAIN"
    save_status(st)
    t0 = time.time()
    if strategy == "deepspeed_zero3":
        try:
            import deepspeed  # noqa: F401
        except ImportError:
            st.stage = "FAILED"
            _log(st, "DeepSpeed not installed. On the GPU cluster: pip install -e '.[deepSpeed]'")
            save_status(st)
            return st
        import torch

        n = torch.cuda.device_count() if torch.cuda.is_available() else 0
        rc = _launch_deepspeed(
            config=config,
            data=data,
            tokenizer=tokenizer,
            deepspeed_config=deepspeed_config,
            output=str(out / "pretrain"),
            num_gpus=n or None,
        )
    elif strategy == "fsdp":
        import torch

        n = torch.cuda.device_count() if torch.cuda.is_available() else 1
        rc = _launch_fsdp(
            config=config,
            data=data,
            tokenizer=tokenizer,
            output=str(out / "pretrain"),
            steps=pretrain_steps,
            nproc=max(n, 1),
        )
    else:
        st.stage = "FAILED"
        _log(st, f"Unsupported strategy for 70B: {strategy}")
        save_status(st)
        return st

    st.metrics["pretrain_seconds"] = round(time.time() - t0, 2)
    st.metrics["pretrain_exit_code"] = rc
    if rc != 0:
        st.stage = "FAILED"
        _log(st, f"Pretrain exited with code {rc}")
        save_status(st)
        return st

    st.stage = "PRETRAINED"
    st.artifacts["pretrain_dir"] = str(out / "pretrain")
    _log(st, "Pretrain stage process completed (weights still require your eval).")
    save_status(st)

    if skip_posttrain:
        save_status(st)
        return st

    # Post-train stages are invoked via existing CLI modules when data is provided.
    # They intentionally do not auto-mark trained=True.
    if sft_data:
        st.stage = "SFT"
        save_status(st)
        rc = subprocess.call(
            [
                sys.executable,
                "-m",
                "om_ai.cli",
                "sft",
                "--config",
                config,
                "--tokenizer",
                tokenizer,
                "--data",
                sft_data,
                "--checkpoint",
                str(out / "pretrain" / "distributed-latest.pt"),
                "--output",
                str(out / "sft"),
            ]
        )
        st.metrics["sft_exit_code"] = rc
        if rc != 0:
            st.stage = "FAILED"
            save_status(st)
            return st
        st.artifacts["sft_dir"] = str(out / "sft")

    if preference_data:
        st.stage = "ALIGNED"
        save_status(st)
        ckpt = st.artifacts.get("sft_dir", st.artifacts.get("pretrain_dir", ""))
        rc = subprocess.call(
            [
                sys.executable,
                "-m",
                "om_ai.cli",
                "dpo",
                "--config",
                config,
                "--tokenizer",
                tokenizer,
                "--data",
                preference_data,
                "--checkpoint",
                str(Path(ckpt) / "sft-latest.pt") if "sft" in ckpt else str(Path(ckpt) / "distributed-latest.pt"),
                "--output",
                str(out / "dpo"),
            ]
        )
        st.metrics["dpo_exit_code"] = rc
        if rc != 0:
            st.stage = "FAILED"
            save_status(st)
            return st
        st.artifacts["dpo_dir"] = str(out / "dpo")
        st.stage = "ALIGNED"

    gates = load_gates(gates_path)
    if benchmark:
        st.stage = "BENCHMARKED"
        save_status(st)
        report_file = str(out / "benchmark_report.json")
        ckpt_candidates = [
            out / "dpo" / "dpo-latest.pt",
            out / "sft" / "sft-latest.pt",
            out / "pretrain" / "distributed-latest.pt",
            out / "pretrain" / "deepspeed",
        ]
        ckpt = next((str(p) for p in ckpt_candidates if p.exists() or p.is_dir()), "")
        if not ckpt:
            st.stage = "FAILED"
            _log(st, "No checkpoint found for benchmarks")
            save_status(st)
            return st
        rc = subprocess.call(
            [
                sys.executable,
                "-m",
                "om_ai.cli",
                "benchmark",
                "--config",
                config,
                "--tokenizer",
                tokenizer,
                "--checkpoint",
                ckpt,
                "--benchmark",
                benchmark,
                "--report",
                report_file,
            ]
        )
        st.metrics["benchmark_exit_code"] = rc
        st.artifacts["benchmark_report"] = report_file
        score = 0.0
        if Path(report_file).is_file():
            try:
                br = json.loads(Path(report_file).read_text())
                score = float(br.get("score", br.get("accuracy", 0.0)) or 0.0)
            except Exception:
                score = 0.0
        st.metrics["benchmark_score"] = score
        min_score = float(gates.get("min_benchmark_score", 0.0))
        if rc == 0 and score >= min_score and min_score > 0:
            st.stage = "PRODUCTION_CANDIDATE"
            st.production_candidate = True
            st.trained = True
            _log(
                st,
                f"Gates passed (score={score} >= {min_score}). "
                "Mark as production candidate only — still do not claim frontier without evidence.",
            )
        else:
            _log(
                st,
                f"Benchmark finished score={score} min={min_score}. "
                "Not marking trained/production (honest gate).",
            )
            st.trained = False
            st.production_candidate = False
            st.stage = "BENCHMARKED"
    else:
        _log(st, "No --benchmark provided; refusing to mark trained=True.")
        st.trained = False

    save_status(st)
    return st
