from __future__ import annotations

from pathlib import Path

from om_ai.backends.om_native import default_native_paths


def test_relative_native_paths_are_resolved_from_repo_root(monkeypatch):
    monkeypatch.setenv("OM_MODEL_CONFIG", "configs/om-1.0-local.json")
    monkeypatch.setenv("OM_MODEL_TOKENIZER", "artifacts/tokenizer-production-65536.json")
    monkeypatch.setenv("OM_MODEL_CHECKPOINT", "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt")
    monkeypatch.delenv("OM_AI_CONFIG", raising=False)
    monkeypatch.delenv("OM_AI_TOKENIZER", raising=False)
    monkeypatch.delenv("OM_AI_CHECKPOINT", raising=False)

    paths = default_native_paths()
    repo_root = Path(__file__).resolve().parents[1]

    assert Path(paths["config"]) == repo_root / "configs/om-1.0-local.json"
    assert Path(paths["tokenizer"]) == repo_root / "artifacts/tokenizer-production-65536.json"
    assert Path(paths["checkpoint"]) == repo_root / "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt"


def test_absolute_native_paths_are_preserved(monkeypatch, tmp_path):
    config = tmp_path / "model.json"
    tokenizer = tmp_path / "tokenizer.json"
    checkpoint = tmp_path / "checkpoint.pt"
    monkeypatch.setenv("OM_MODEL_CONFIG", str(config))
    monkeypatch.setenv("OM_MODEL_TOKENIZER", str(tokenizer))
    monkeypatch.setenv("OM_MODEL_CHECKPOINT", str(checkpoint))
    monkeypatch.delenv("OM_AI_CONFIG", raising=False)
    monkeypatch.delenv("OM_AI_TOKENIZER", raising=False)
    monkeypatch.delenv("OM_AI_CHECKPOINT", raising=False)

    paths = default_native_paths()

    assert Path(paths["config"]) == config
    assert Path(paths["tokenizer"]) == tokenizer
    assert Path(paths["checkpoint"]) == checkpoint
