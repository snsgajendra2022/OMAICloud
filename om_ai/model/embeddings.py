"""Token + positional embeddings (RoPE applied in attention)."""
from __future__ import annotations

import torch.nn as nn

from om_ai.core.config import ModelConfig
from om_ai.model.rope import apply_rope, precompute_rope

__all__ = ["TokenEmbedding", "apply_rope", "precompute_rope"]


class TokenEmbedding(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.d_model)

    def forward(self, idx):
        return self.tok_emb(idx)
