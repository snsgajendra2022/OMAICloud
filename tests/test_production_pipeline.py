"""OMCausalLoss + 3-stage production pipeline inventory tests."""
from __future__ import annotations

import torch

from om_ai.model.causal_loss import OMCausalLoss, build_assistant_only_labels, causal_cross_entropy
from om_ai.model.transformer import OMTransformer
from om_ai.core.config import ModelConfig
from om_ai.training.production_pipeline import inventory, pick_training_device, run_stage


def test_om_causal_loss_shift_matches_manual():
    logits = torch.randn(2, 5, 11)
    labels = torch.randint(0, 11, (2, 5))
    labels[:, :2] = -100
    loss_mod = OMCausalLoss(auto_shift=True)(logits, labels)
    shift_logits = logits[:, :-1].contiguous()
    shift_labels = labels[:, 1:].contiguous()
    manual = torch.nn.functional.cross_entropy(
        shift_logits.view(-1, 11),
        shift_labels.view(-1),
        ignore_index=-100,
    )
    assert torch.allclose(loss_mod, manual)


def test_assistant_only_labels_mask_prompt():
    ids = [1, 2, 3, 4, 5, 6]
    labels = build_assistant_only_labels(ids, prompt_len=4)
    assert labels[:4] == [-100, -100, -100, -100]
    assert labels[4:] == [5, 6]


def test_model_forward_uses_causal_loss_with_full_labels():
    cfg = ModelConfig(
        vocab_size=64,
        max_seq_len=16,
        n_layers=1,
        n_heads=2,
        n_kv_heads=2,
        d_model=16,
        d_ff=32,
    )
    m = OMTransformer(cfg)
    x = torch.randint(0, 64, (1, 8))
    labels = x.clone()
    labels[:, :3] = -100
    out = m(x, labels=labels)
    assert out["loss"] is not None
    assert torch.isfinite(out["loss"])


def test_pipeline_inventory_reports_bottleneck():
    inv = inventory()
    assert inv.total_data_bytes > 0
    assert inv.chat_sft_rows >= 0
    assert "bottleneck" in inv.bottleneck.lower() or len(inv.bottleneck) > 10
    assert inv.architecture.get("rope") is True
    assert inv.architecture.get("om_causal_loss") is True


def test_run_stage_dry_run_sft():
    out = run_stage("sft", dry_run=True)
    assert out["dry_run"] is True
    assert "sft" in out["cmd"]
    assert out["device"] == pick_training_device() or out["device"] in {"mps", "cpu", "cuda"}
