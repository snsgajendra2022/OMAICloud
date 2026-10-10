from pathlib import Path

from om_ai.core.config import ModelConfig


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> ModelConfig:
    return ModelConfig.from_json(ROOT / "configs" / name)


def test_om_70b_preset_is_about_69b_parameters() -> None:
    cfg = load("70b.json")
    assert cfg.n_layers == 80
    assert cfg.d_model == 8192
    assert cfg.n_heads == 64
    assert cfg.n_kv_heads == 8
    assert cfg.max_seq_len == 8192
    assert 68_000_000_000 <= cfg.parameter_estimate() <= 71_000_000_000


def test_om_200b_preset_is_about_192b_parameters() -> None:
    cfg = load("om-2.0-200b.json")
    assert cfg.n_layers == 96
    assert cfg.d_model == 12288
    assert cfg.n_heads == 96
    assert cfg.n_kv_heads == 8
    assert cfg.d_ff == 45056
    assert cfg.max_seq_len == 4096
    assert cfg.gradient_checkpointing is True
    assert cfg.d_model % cfg.n_heads == 0
    assert cfg.n_heads % cfg.n_kv_heads == 0
    assert 190_000_000_000 <= cfg.parameter_estimate() <= 193_000_000_000
