"""Preflight checks for large-scale OM training (especially 70B).

Runs on any machine. GPU cluster checks fail clearly on CPU/Mac so operators
know the job is not ready — software alone cannot invent 70B weights.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = True


@dataclass
class PreflightReport:
    ok: bool
    checks: list[CheckResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [asdict(c) for c in self.checks],
            "summary": self.summary,
        }


def _add(checks: list[CheckResult], name: str, ok: bool, detail: str, required: bool = True) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, required=required))


def check_corpus(data_path: str | Path, *, min_bytes: int = 1_000_000) -> CheckResult:
    path = Path(data_path)
    if not path.exists():
        return CheckResult("corpus.exists", False, f"missing: {path}")
    if path.is_file():
        size = path.stat().st_size
        files = 1
    else:
        files = 0
        size = 0
        for p in path.rglob("*"):
            if p.is_file():
                files += 1
                size += p.stat().st_size
    if size < min_bytes:
        return CheckResult(
            "corpus.size",
            False,
            f"{files} file(s), {size} bytes < min_bytes={min_bytes}. "
            "70B pretraining needs a licensed multi-trillion-token-scale corpus; "
            "this gate only checks a minimum presence floor.",
        )
    return CheckResult("corpus", True, f"{files} file(s), {size} bytes at {path}")


def check_tokenizer(tokenizer_path: str | Path, *, expect_vocab: int | None = None) -> CheckResult:
    path = Path(tokenizer_path)
    if not path.is_file():
        return CheckResult("tokenizer.exists", False, f"missing: {path}")
    try:
        from om_ai.tokenizer import ByteBPETokenizer

        tok = ByteBPETokenizer.load(path)
        n = len(tok.vocab)
    except Exception as exc:
        return CheckResult("tokenizer.load", False, f"failed to load: {exc}")
    # Soft floor: tokenizer should not be dramatically smaller than the config vocab.
    if expect_vocab and expect_vocab >= 1000 and n < max(64, expect_vocab // 4):
        return CheckResult(
            "tokenizer.vocab",
            False,
            f"vocab_size={n} looks too small vs config vocab_size={expect_vocab}",
        )
    return CheckResult("tokenizer", True, f"vocab_size={n} path={path}")


def check_config(config_path: str | Path) -> CheckResult:
    path = Path(config_path)
    if not path.is_file():
        return CheckResult("config.exists", False, f"missing: {path}")
    try:
        from om_ai.core.config import ModelConfig

        cfg = ModelConfig.from_json(path)
        est = cfg.parameter_estimate()
    except Exception as exc:
        return CheckResult("config.load", False, str(exc))
    return CheckResult(
        "config",
        True,
        f"layers={cfg.n_layers} d_model={cfg.d_model} ~{est/1e9:.1f}B params (architecture only)",
    )


def check_cuda(
    *,
    min_gpus: int = 8,
    min_vram_gb: float = 40.0,
    allow_cpu: bool = False,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    try:
        import torch
    except ImportError:
        _add(checks, "torch", False, "torch not installed")
        return checks

    cuda = torch.cuda.is_available()
    if not cuda:
        _add(
            checks,
            "cuda",
            allow_cpu,
            "CUDA not available. Mac/CPU can develop software and run tiny smoke jobs; "
            "final OM-70B pretraining needs a GPU cluster.",
            required=not allow_cpu,
        )
        return checks

    n = torch.cuda.device_count()
    _add(checks, "cuda.available", True, f"torch.cuda device_count={n}")
    _add(
        checks,
        "cuda.gpu_count",
        n >= min_gpus,
        f"gpus={n} min_gpus={min_gpus}",
    )
    vrams = []
    for i in range(n):
        props = torch.cuda.get_device_properties(i)
        gb = props.total_memory / (1024**3)
        vrams.append(gb)
        if gb < min_vram_gb:
            _add(
                checks,
                f"cuda.vram.{i}",
                False,
                f"{props.name}: {gb:.1f} GiB < min_vram_gb={min_vram_gb}",
            )
    if vrams and all(v >= min_vram_gb for v in vrams):
        _add(checks, "cuda.vram", True, f"all GPUs >= {min_vram_gb} GiB: {['%.1f' % v for v in vrams]}")
    return checks


def check_distributed_env(*, require_multi_node_vars: bool = False) -> CheckResult:
    rank = os.getenv("RANK")
    world = os.getenv("WORLD_SIZE")
    master = os.getenv("MASTER_ADDR")
    detail = f"RANK={rank} WORLD_SIZE={world} MASTER_ADDR={master} LOCAL_RANK={os.getenv('LOCAL_RANK')}"
    if require_multi_node_vars and (not world or not master):
        return CheckResult(
            "distributed.env",
            False,
            f"multi-node vars missing ({detail}). Set via Slurm/K8s/torchrun.",
        )
    if world and int(world) < 1:
        return CheckResult("distributed.env", False, detail)
    return CheckResult(
        "distributed.env",
        True,
        detail if world else "single-process / will be set by torchrun or deepspeed launcher",
        required=False,
    )


def check_disk(output_path: str | Path, *, min_free_gb: float = 500.0) -> CheckResult:
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024**3)
    ok = free_gb >= min_free_gb
    return CheckResult(
        "disk.free",
        ok,
        f"free={free_gb:.1f} GiB at {path} (min_free_gb={min_free_gb})",
    )


def check_deepspeed_optional() -> CheckResult:
    try:
        import deepspeed  # noqa: F401

        return CheckResult("deepspeed", True, "deepspeed import ok", required=False)
    except ImportError:
        return CheckResult(
            "deepspeed",
            False,
            "not installed — pip install -e '.[deepSpeed]' on the training cluster",
            required=False,
        )


def run_preflight(
    *,
    data: str | Path,
    tokenizer: str | Path,
    output: str | Path,
    config: str | Path = "configs/70b.json",
    min_gpus: int = 8,
    min_vram_gb: float = 40.0,
    min_free_gb: float = 500.0,
    min_corpus_bytes: int = 1_000_000,
    allow_cpu: bool = False,
    require_distributed_env: bool = False,
    manifest: str | Path | None = None,
) -> PreflightReport:
    checks: list[CheckResult] = []
    checks.append(check_config(config))
    expect_vocab = None
    try:
        from om_ai.core.config import ModelConfig

        expect_vocab = ModelConfig.from_json(config).vocab_size
    except Exception:
        pass
    checks.append(check_corpus(data, min_bytes=min_corpus_bytes))
    checks.append(check_tokenizer(tokenizer, expect_vocab=expect_vocab))
    if manifest:
        try:
            from om_ai.corpus import CorpusService

            result = CorpusService().validate_manifest(manifest)
            checks.append(
                CheckResult("corpus.manifest", True, f"sources={result.get('sources')}")
            )
        except Exception as exc:
            checks.append(CheckResult("corpus.manifest", False, str(exc)))
    checks.extend(
        check_cuda(min_gpus=min_gpus, min_vram_gb=min_vram_gb, allow_cpu=allow_cpu)
    )
    checks.append(check_distributed_env(require_multi_node_vars=require_distributed_env))
    checks.append(check_disk(output, min_free_gb=min_free_gb))
    checks.append(check_deepspeed_optional())

    required_ok = all(c.ok for c in checks if c.required)
    summary = {
        "ready_to_train": required_ok,
        "note": (
            "Passing preflight means the *software path* can start. "
            "It does not mean OM-70B is trained or frontier-capable."
        ),
    }
    return PreflightReport(ok=required_ok, checks=checks, summary=summary)


def write_report(report: PreflightReport, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2))
    return out
