"""Tests for 70B launcher helpers (safe on CPU/Mac)."""
from __future__ import annotations

import json
from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.training.partition_init import create_om_transformer, recommended_strategy
from om_ai.training.preflight import run_preflight


def test_recommended_strategy_tiny_is_eager():
    assert recommended_strategy(10_000_000) == "eager"
    assert recommended_strategy(70_000_000_000) in {"deepspeed_zero3", "meta"}


def test_meta_init_tiny_stays_on_meta():
    cfg = ModelConfig(
        vocab_size=64,
        max_seq_len=32,
        n_layers=2,
        n_heads=4,
        n_kv_heads=4,
        d_model=32,
        d_ff=64,
    )
    model = create_om_transformer(cfg, strategy="meta")
    assert next(model.parameters()).device.type == "meta"
    assert model.cfg.n_layers == 2


def test_eager_init_still_works():
    cfg = ModelConfig(
        vocab_size=64,
        max_seq_len=32,
        n_layers=1,
        n_heads=4,
        n_kv_heads=4,
        d_model=32,
        d_ff=64,
    )
    model = create_om_transformer(cfg, strategy="eager")
    x = torch.randint(0, 64, (1, 8))
    out = model(x, labels=x)
    assert out["loss"] is not None


def test_preflight_reports_missing_cuda_on_cpu(tmp_path: Path):
    data = tmp_path / "corp.txt"
    data.write_text("hello world " * 1000)
    tok = Path("artifacts/demo/tokenizer.json")
    if not tok.is_file():
        # skip soft if demo missing
        return
    report = run_preflight(
        data=data,
        tokenizer=tok,
        output=tmp_path / "out",
        config="configs/tiny.json",
        min_gpus=8,
        min_vram_gb=40,
        min_free_gb=0.001,
        min_corpus_bytes=10,
        allow_cpu=False,
    )
    # On Mac/CPU this should fail required CUDA checks.
    if not torch.cuda.is_available():
        assert report.ok is False
        assert any(c.name.startswith("cuda") and not c.ok for c in report.checks)


def test_train_70b_cli_preflight_only(tmp_path: Path):
    from om_ai.training.train_70b import run_train_70b

    data = tmp_path / "corp.txt"
    data.write_text("om ai corpus " * 2000)
    tok = Path("artifacts/demo/tokenizer.json")
    if not tok.is_file():
        return
    st = run_train_70b(
        data=str(data),
        tokenizer=str(tok),
        output=str(tmp_path / "ck"),
        config="configs/tiny.json",
        preflight_only=True,
        min_gpus=1,
        min_vram_gb=0.1,
        min_free_gb=0.001,
        min_corpus_bytes=10,
        allow_cpu=True,
    )
    assert Path(st.artifacts["preflight_report"]).is_file()
    report = json.loads(Path(st.artifacts["preflight_report"]).read_text())
    assert report["ok"] is True
    assert st.trained is False
