from __future__ import annotations
import torch


def precompute_rope(head_dim: int, seq_len: int, theta: float, device=None, dtype=torch.float32):
    if head_dim % 2:
        raise ValueError("RoPE head_dim must be even")
    inv_freq = 1.0 / (theta ** (torch.arange(0, head_dim, 2, device=device, dtype=torch.float32) / head_dim))
    positions = torch.arange(seq_len, device=device, dtype=torch.float32)
    freqs = torch.outer(positions, inv_freq)
    return freqs.cos().to(dtype), freqs.sin().to(dtype)


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1 = x[..., ::2]
    x2 = x[..., 1::2]
    out = torch.stack((-x2, x1), dim=-1)
    return out.flatten(-2)


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, offset: int = 0) -> torch.Tensor:
    # x: [B,H,T,D]
    t = x.size(-2)
    cos = cos[offset: offset + t].repeat_interleave(2, dim=-1)[None, None, :, :]
    sin = sin[offset: offset + t].repeat_interleave(2, dim=-1)[None, None, :, :]
    return (x * cos) + (rotate_half(x) * sin)
