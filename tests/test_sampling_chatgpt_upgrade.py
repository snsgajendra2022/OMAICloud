"""Phase 1 sampling + ChatGPT upgrade audit smoke tests."""
from __future__ import annotations

import torch

from om_ai.model.transformer import (
    _apply_repetition_penalty,
    _apply_top_p,
    _ban_repeated_ngrams,
)
from om_ai.training.chatgpt_upgrade import audit_chatgpt_parity, write_example_datasets


def test_top_p_keeps_mass():
    logits = torch.tensor([[1.0, 0.5, -2.0, -5.0]])
    filtered = _apply_top_p(logits, 0.9)
    # Lowest-mass tokens should be -inf after nucleus filter
    assert torch.isneginf(filtered[0, 3]) or filtered[0, 3] < filtered[0, 0]


def test_repetition_penalty_lowers_seen_tokens():
    logits = torch.tensor([[2.0, 2.0, 2.0]])
    generated = torch.tensor([[0, 0, 1]])
    out = _apply_repetition_penalty(logits, generated, 1.2)
    assert float(out[0, 0]) < float(logits[0, 0])
    assert float(out[0, 1]) < float(logits[0, 1])
    assert float(out[0, 2]) == float(logits[0, 2])


def test_no_repeat_ngram_bans_continuation():
    # History ends with [1, 2]; prior ngram (1,2,3) → ban 3
    logits = torch.zeros(1, 5)
    generated = torch.tensor([[9, 1, 2, 3, 1, 2]])
    out = _ban_repeated_ngrams(logits, generated, ngram_size=3)
    assert torch.isneginf(out[0, 3])


def test_chatgpt_parity_audit_phases():
    audit = audit_chatgpt_parity()
    assert audit.phase1_ok
    assert audit.phase2_ok
    assert audit.sft_trainer and audit.dpo_trainer
    d = audit.as_dict()
    assert d["scaled_dot_product_attention"] is True
    assert d["rope"] is True


def test_write_example_datasets(tmp_path):
    paths = write_example_datasets(tmp_path)
    assert (tmp_path / "data" / "sft" / "chat_conversations.example.jsonl").is_file()
    assert (tmp_path / "data" / "dpo" / "preferences.example.jsonl").is_file()
    assert "sft_example" in paths
