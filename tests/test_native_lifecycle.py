from __future__ import annotations

import json

from om_ai.native_lifecycle import load_config, model_info


def test_native_100m_config_has_valid_dimensions():
    cfg = load_config("configs/om-1.1-100m.json")
    assert cfg.d_model % cfg.n_heads == 0
    assert cfg.n_heads % cfg.n_kv_heads == 0
    assert cfg.max_seq_len >= 2
    assert 50_000_000 < cfg.parameter_estimate() < 150_000_000


def test_model_info_does_not_claim_trained_or_production_ready():
    result = model_info("configs/om-1.1-100m.json")
    assert result["model_family"] == "native_om"
    assert result["weights_available"] is False
    assert result["production_ready"] is False
    assert result["parameters_estimated"] > 0
