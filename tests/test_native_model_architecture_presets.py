from pathlib import Path

from om_ai.core.config import ModelConfig


ROOT = Path(__file__).resolve().parents[1]


def load_preset(name: str) -> ModelConfig:
    return ModelConfig.from_json(ROOT / "configs" / name)


def test_om_11_300m_preset_matches_native_config_schema() -> None:
    cfg = load_preset("om-1.1-300m.json")

    assert cfg.vocab_size == 65_536
    assert cfg.max_seq_len == 2_048
    assert cfg.n_layers == 16
    assert cfg.d_model == 1_024
    assert cfg.n_heads == 16
    assert cfg.n_kv_heads == 4
    assert cfg.d_ff == 3_584
    assert cfg.gradient_checkpointing is True
    assert cfg.d_model % cfg.n_heads == 0
    assert cfg.n_heads % cfg.n_kv_heads == 0


def test_om_11_300m_estimated_parameter_count_is_in_expected_range() -> None:
    cfg = load_preset("om-1.1-300m.json")

    # Estimate from the repository's actual ModelConfig implementation.
    assert 280_000_000 <= cfg.parameter_estimate() <= 290_000_000


def test_om_11_1b_preset_matches_native_config_schema() -> None:
    cfg = load_preset("om-1.1-1b.json")

    assert cfg.max_seq_len == 2_048
    assert cfg.n_layers == 24
    assert cfg.d_model == 2_048
    assert cfg.n_heads == 16
    assert cfg.n_kv_heads == 8
    assert cfg.d_ff == 5_504
    assert cfg.gradient_checkpointing is True
    assert cfg.d_model % cfg.n_heads == 0
    assert cfg.n_heads % cfg.n_kv_heads == 0


def test_om_11_1b_estimated_parameter_count_is_about_1_25b() -> None:
    cfg = load_preset("om-1.1-1b.json")

    # This is an architecture estimate, not evidence of a trained model.
    assert 1_200_000_000 <= cfg.parameter_estimate() <= 1_300_000_000
