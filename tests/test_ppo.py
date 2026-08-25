"""Smoke tests for PPO / RLHF infrastructure."""
from __future__ import annotations

import copy

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.training.ppo import (
    PPOConfig,
    PPOTrainer,
    Rollout,
    RolloutBuffer,
    ValueHead,
    compute_advantages,
)


def test_ppo_train_epoch_smoke():
    cfg = ModelConfig(
        vocab_size=128,
        d_model=32,
        n_layers=2,
        n_heads=4,
        n_kv_heads=2,
        d_ff=64,
        max_seq_len=64,
    )
    policy = OMTransformer(cfg)
    ref = copy.deepcopy(policy)
    value_head = ValueHead(cfg.d_model)
    trainer = PPOTrainer(policy, value_head, ref, PPOConfig(ppo_epochs=1, lr=1e-4), device=torch.device("cpu"))

    prompt_ids = [1, 2, 3]
    response_ids = [4, 5, 6]
    full = torch.tensor([prompt_ids + response_ids], dtype=torch.long)
    resp_mask = torch.zeros_like(full, dtype=torch.bool)
    resp_mask[0, len(prompt_ids) :] = True
    with torch.no_grad():
        lp = trainer.compute_logprobs(policy, full, resp_mask).tolist()
        ref_lp = trainer.compute_logprobs(ref, full, resp_mask).tolist()
        hidden = policy(full, use_cache=False)["last_hidden_state"]
        vals = value_head(hidden[:, len(prompt_ids) :, :]).squeeze(0).tolist()
        if isinstance(vals, float):
            vals = [vals]

    t = len(response_ids)
    rollout = Rollout(
        prompt_ids=prompt_ids,
        response_ids=response_ids,
        logprobs=(lp + [0.0] * t)[:t],
        ref_logprobs=(ref_lp + [0.0] * t)[:t],
        values=(list(vals) + [0.0] * t)[:t],
        reward=1.0,
    )
    compute_advantages(rollout)
    buf = RolloutBuffer(max_rollouts=1)
    buf.add(rollout)
    stats = trainer.train_epoch(buf)
    assert "policy_loss" in stats
    assert stats["steps"] >= 1
    assert "last_hidden_state" in policy(full, use_cache=False)
