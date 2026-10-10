from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from om_ai.core.config import ModelConfig
from .rope import precompute_rope, apply_rope


@dataclass
class KVCache:
    key: torch.Tensor
    value: torch.Tensor


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dtype = x.dtype
        x = x.float()
        var = x.pow(2).mean(dim=-1, keepdim=True)
        x = x * torch.rsqrt(var + self.eps)
        return (self.weight * x).to(dtype)


def make_norm(cfg: ModelConfig) -> nn.Module:
    if cfg.use_rmsnorm:
        return RMSNorm(cfg.d_model)
    return nn.LayerNorm(cfg.d_model)


class SwiGLU(nn.Module):
    def __init__(self, d_model: int, d_ff: int, bias: bool = False):
        super().__init__()
        self.gate = nn.Linear(d_model, d_ff, bias=bias)
        self.up = nn.Linear(d_model, d_ff, bias=bias)
        self.down = nn.Linear(d_ff, d_model, bias=bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(F.silu(self.gate(x)) * self.up(x))


def _enable_flash_sdp() -> None:
    try:
        if hasattr(torch.backends.cuda, "enable_flash_sdp"):
            torch.backends.cuda.enable_flash_sdp(True)
            torch.backends.cuda.enable_mem_efficient_sdp(True)
            torch.backends.cuda.enable_math_sdp(True)
    except Exception:
        pass


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.n_heads = cfg.n_heads
        self.n_kv_heads = cfg.n_kv_heads or cfg.n_heads
        self.head_dim = cfg.d_model // cfg.n_heads
        self.kv_repeat = self.n_heads // self.n_kv_heads
        self.q_proj = nn.Linear(cfg.d_model, cfg.n_heads * self.head_dim, bias=cfg.bias)
        self.k_proj = nn.Linear(cfg.d_model, self.n_kv_heads * self.head_dim, bias=cfg.bias)
        self.v_proj = nn.Linear(cfg.d_model, self.n_kv_heads * self.head_dim, bias=cfg.bias)
        self.o_proj = nn.Linear(cfg.n_heads * self.head_dim, cfg.d_model, bias=cfg.bias)
        self.dropout = cfg.dropout
        self.rope_theta = cfg.rope_theta * cfg.rope_scaling
        self.max_seq_len = cfg.max_seq_len
        _enable_flash_sdp()

    def _shape(self, x: torch.Tensor, heads: int) -> torch.Tensor:
        b, t, _ = x.shape
        return x.view(b, t, heads, self.head_dim).transpose(1, 2)

    def forward(self, x: torch.Tensor, cache: KVCache | None = None, use_cache: bool = False):
        _, t, _ = x.shape
        q = self._shape(self.q_proj(x), self.n_heads)
        k = self._shape(self.k_proj(x), self.n_kv_heads)
        v = self._shape(self.v_proj(x), self.n_kv_heads)

        past_len = 0 if cache is None else cache.key.size(-2)
        cos, sin = precompute_rope(
            self.head_dim,
            max(self.max_seq_len, past_len + t),
            self.rope_theta,
            device=x.device,
            dtype=q.dtype,
        )
        q = apply_rope(q, cos, sin, offset=past_len)
        k = apply_rope(k, cos, sin, offset=past_len)

        if cache is not None:
            k = torch.cat([cache.key, k], dim=-2)
            v = torch.cat([cache.value, v], dim=-2)
        new_cache = KVCache(k.detach(), v.detach()) if use_cache else None

        if self.kv_repeat > 1:
            k_attn = k.repeat_interleave(self.kv_repeat, dim=1)
            v_attn = v.repeat_interleave(self.kv_repeat, dim=1)
        else:
            k_attn, v_attn = k, v

        is_causal = cache is None and t > 1
        y = F.scaled_dot_product_attention(
            q, k_attn, v_attn,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=is_causal,
        )
        b = x.size(0)
        y = y.transpose(1, 2).contiguous().view(b, t, self.n_heads * self.head_dim)
        return self.o_proj(y), new_cache


class CrossAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.n_heads = cfg.n_heads
        self.head_dim = cfg.d_model // cfg.n_heads
        self.q_proj = nn.Linear(cfg.d_model, cfg.d_model, bias=cfg.bias)
        self.k_proj = nn.Linear(cfg.d_model, cfg.d_model, bias=cfg.bias)
        self.v_proj = nn.Linear(cfg.d_model, cfg.d_model, bias=cfg.bias)
        self.o_proj = nn.Linear(cfg.d_model, cfg.d_model, bias=cfg.bias)
        self.dropout = cfg.dropout

    def _shape(self, x: torch.Tensor) -> torch.Tensor:
        b, t, _ = x.shape
        return x.view(b, t, self.n_heads, self.head_dim).transpose(1, 2)

    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        q = self._shape(self.q_proj(x))
        k = self._shape(self.k_proj(context))
        v = self._shape(self.v_proj(context))
        y = F.scaled_dot_product_attention(
            q, k, v,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=False,
        )
        b, _, t, _ = y.shape
        return self.o_proj(y.transpose(1, 2).contiguous().view(b, t, -1))


class TransformerBlock(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.ln1 = make_norm(cfg)
        self.attn = CausalSelfAttention(cfg)
        self.cross_attn = CrossAttention(cfg) if cfg.cross_attention else None
        self.ln_cross = make_norm(cfg) if cfg.cross_attention else None
        self.ln2 = make_norm(cfg)
        self.ff = SwiGLU(cfg.d_model, cfg.d_ff, bias=cfg.bias)
        self.drop = nn.Dropout(cfg.dropout)

    def forward(
        self,
        x: torch.Tensor,
        cache: KVCache | None = None,
        use_cache: bool = False,
        encoder_hidden_states: torch.Tensor | None = None,
    ):
        a, new_cache = self.attn(self.ln1(x), cache=cache, use_cache=use_cache)
        x = x + self.drop(a)
        if self.cross_attn is not None and encoder_hidden_states is not None:
            x = x + self.drop(self.cross_attn(self.ln_cross(x), encoder_hidden_states))
        x = x + self.drop(self.ff(self.ln2(x)))
        return x, new_cache


def _apply_top_p(logits: torch.Tensor, top_p: float) -> torch.Tensor:
    """Nucleus sampling — keep smallest set of tokens with cumprob >= top_p."""
    if top_p >= 1.0:
        return logits
    top_p = float(max(1e-6, min(1.0, top_p)))
    sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
    probs = F.softmax(sorted_logits, dim=-1)
    cum = torch.cumsum(probs, dim=-1)
    # Remove tokens with cumulative probability above the threshold (keep first over)
    mask = cum > top_p
    mask[..., 1:] = mask[..., :-1].clone()
    mask[..., 0] = False
    sorted_logits = sorted_logits.masked_fill(mask, float("-inf"))
    return torch.zeros_like(logits).scatter_(-1, sorted_idx, sorted_logits)


def _apply_repetition_penalty(
    logits: torch.Tensor,
    generated: torch.Tensor,
    penalty: float,
    *,
    window: int = 0,
) -> torch.Tensor:
    """HF-style repetition penalty on tokens already seen (optionally last `window`)."""
    if penalty == 1.0 or generated.numel() == 0:
        return logits
    penalty = float(max(1.0, penalty))
    out = logits.clone()
    for b in range(generated.size(0)):
        hist = generated[b]
        if window and window > 0 and hist.numel() > window:
            hist = hist[-window:]
        unique = torch.unique(hist)
        # Vectorized: positive logits / penalty, negative * penalty
        vals = out[b, unique]
        out[b, unique] = torch.where(vals > 0, vals / penalty, vals * penalty)
    return out


def _ban_repeated_ngrams(
    logits: torch.Tensor,
    generated: torch.Tensor,
    ngram_size: int,
) -> torch.Tensor:
    """Block tokens that would complete an n-gram already present in the sequence."""
    if ngram_size <= 0 or generated.size(1) < ngram_size:
        return logits
    out = logits.clone()
    for b in range(generated.size(0)):
        ids = generated[b].tolist()
        if len(ids) < ngram_size:
            continue
        prefix = tuple(ids[-(ngram_size - 1) :]) if ngram_size > 1 else tuple()
        banned: set[int] = set()
        for i in range(len(ids) - ngram_size + 1):
            gram = tuple(ids[i : i + ngram_size])
            if gram[:-1] == prefix:
                banned.add(int(gram[-1]))
        for tok in banned:
            out[b, tok] = float("-inf")
    return out


def _safe_multinomial(probs: torch.Tensor) -> torch.Tensor:
    """Sample with NaN/Inf guard — fall back to argmax if distribution collapses."""
    if not torch.isfinite(probs).all() or float(probs.sum()) <= 0:
        # Recover from all -inf logits
        flat = probs.view(probs.size(0), -1)
        return torch.argmax(flat, dim=-1, keepdim=True)
    return torch.multinomial(probs, num_samples=1)


class OMTransformer(nn.Module):
    def __init__(self, cfg: ModelConfig, *, skip_init: bool = False):
        super().__init__()
        self.cfg = cfg
        self.token_embedding = nn.Embedding(cfg.vocab_size, cfg.d_model)
        self.blocks = nn.ModuleList([TransformerBlock(cfg) for _ in range(cfg.n_layers)])
        self.final_norm = make_norm(cfg)
        self.lm_head = nn.Linear(cfg.d_model, cfg.vocab_size, bias=False)
        if cfg.tie_embeddings:
            self.lm_head.weight = self.token_embedding.weight
        self.gradient_checkpointing = cfg.gradient_checkpointing
        if not skip_init:
            self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=self.cfg.initializer_range)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def set_gradient_checkpointing(self, enabled: bool) -> None:
        self.gradient_checkpointing = enabled

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: torch.Tensor | None = None,
        caches: list[KVCache | None] | None = None,
        use_cache: bool = False,
        encoder_hidden_states: torch.Tensor | None = None,
        output_hidden_states: bool = False,
        shift_labels: bool = False,
    ):
        if input_ids.size(1) > self.cfg.max_seq_len and caches is None:
            raise ValueError(f"sequence length exceeds max_seq_len={self.cfg.max_seq_len}")
        x = self.token_embedding(input_ids)
        if caches is None:
            caches = [None] * len(self.blocks)
        new_caches: list[KVCache | None] = []
        for block, cache in zip(self.blocks, caches):
            if self.gradient_checkpointing and self.training and cache is None and not use_cache:
                def _run(h, enc=encoder_hidden_states, blk=block):
                    y, _ = blk(h, cache=None, use_cache=False, encoder_hidden_states=enc)
                    return y
                x = checkpoint(_run, x, use_reentrant=False)
                new_caches.append(None)
            else:
                x, nc = block(
                    x,
                    cache=cache,
                    use_cache=use_cache,
                    encoder_hidden_states=encoder_hidden_states,
                )
                new_caches.append(nc)
        logits = self.lm_head(self.final_norm(x))
        loss = None
        if labels is not None:
            from om_ai.model.causal_loss import causal_cross_entropy

            # Training datasets in this repository already align x=ids[:-1]
            # with y=labels[1:]. Auto-shifting again silently trains against the
            # wrong token positions and can produce incoherent generations. Full-
            # sequence callers must explicitly opt in with shift_labels=True.
            loss = causal_cross_entropy(
                logits,
                labels,
                ignore_index=-100,
                shift=shift_labels,
            )
        result = {
            "logits": logits,
            "loss": loss,
            "caches": new_caches if use_cache else None,
            # Always expose final block states for critics (PPO value head, etc.).
            "last_hidden_state": x,
        }
        if output_hidden_states:
            result["hidden_states"] = x
        return result

    def _sample_next(
        self,
        logits: torch.Tensor,
        generated: torch.Tensor,
        temperature: float,
        top_k: int,
        top_p: float,
        repetition_penalty: float,
        *,
        no_repeat_ngram_size: int = 0,
        repetition_window: int = 0,
    ) -> torch.Tensor:
        logits = _apply_repetition_penalty(
            logits, generated, repetition_penalty, window=repetition_window
        )
        logits = _ban_repeated_ngrams(logits, generated, no_repeat_ngram_size)
        if temperature <= 0:
            return torch.argmax(logits, dim=-1, keepdim=True)
        logits_t = logits / max(float(temperature), 1e-8)
        if top_k > 0:
            k = min(int(top_k), logits_t.size(-1))
            values, _ = torch.topk(logits_t, k)
            cutoff = values[:, -1].unsqueeze(-1)
            logits_t = logits_t.masked_fill(logits_t < cutoff, float("-inf"))
        logits_t = _apply_top_p(logits_t, top_p)
        # Numerical safety before softmax
        logits_t = torch.nan_to_num(logits_t, nan=float("-inf"), posinf=1e4, neginf=float("-inf"))
        # If every logit is -inf, fall back to uniform over vocab
        finite = torch.isfinite(logits_t)
        if not finite.any():
            logits_t = torch.zeros_like(logits_t)
        probs = F.softmax(logits_t, dim=-1)
        return _safe_multinomial(probs)

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        eos_token_id: int | None = None,
        stop_token_ids: list[int] | None = None,
        min_new_tokens: int = 0,
        encoder_hidden_states: torch.Tensor | None = None,
        no_repeat_ngram_size: int = 3,
        repetition_window: int = 128,
    ) -> torch.Tensor:
        self.eval()
        stops = set(stop_token_ids or [])
        if eos_token_id is not None:
            stops.add(eos_token_id)
        min_new_tokens = max(0, int(min_new_tokens))
        if input_ids.size(1) > self.cfg.max_seq_len:
            input_ids = input_ids[:, -self.cfg.max_seq_len :]
        out = self.forward(input_ids, use_cache=True, encoder_hidden_states=encoder_hidden_states)
        caches = out["caches"]
        generated = input_ids
        logits = out["logits"][:, -1, :]
        for step in range(max_new_tokens):
            step_logits = logits
            if step < min_new_tokens and stops:
                step_logits = step_logits.clone()
                for sid in stops:
                    step_logits[:, int(sid)] = float("-inf")
            next_token = self._sample_next(
                step_logits,
                generated,
                temperature,
                top_k,
                top_p,
                repetition_penalty,
                no_repeat_ngram_size=no_repeat_ngram_size,
                repetition_window=repetition_window,
            )
            generated = torch.cat([generated, next_token], dim=1)
            if (
                step >= min_new_tokens
                and stops
                and all(int(t) in stops for t in next_token.view(-1).tolist())
            ):
                break
            out = self.forward(
                next_token,
                caches=caches,
                use_cache=True,
                encoder_hidden_states=encoder_hidden_states,
            )
            caches = out["caches"]
            logits = out["logits"][:, -1, :]
        return generated

    @torch.no_grad()
    def generate_stream(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        eos_token_id: int | None = None,
        stop_token_ids: list[int] | None = None,
        min_new_tokens: int = 0,
        encoder_hidden_states: torch.Tensor | None = None,
        no_repeat_ngram_size: int = 3,
        repetition_window: int = 128,
    ) -> Iterator[torch.Tensor]:
        self.eval()
        stops = set(stop_token_ids or [])
        if eos_token_id is not None:
            stops.add(eos_token_id)
        min_new_tokens = max(0, int(min_new_tokens))
        if input_ids.size(1) > self.cfg.max_seq_len:
            input_ids = input_ids[:, -self.cfg.max_seq_len :]
        out = self.forward(input_ids, use_cache=True, encoder_hidden_states=encoder_hidden_states)
        caches = out["caches"]
        generated = input_ids
        logits = out["logits"][:, -1, :]
        for step in range(max_new_tokens):
            step_logits = logits
            if step < min_new_tokens and stops:
                step_logits = step_logits.clone()
                for sid in stops:
                    step_logits[:, int(sid)] = float("-inf")
            next_token = self._sample_next(
                step_logits,
                generated,
                temperature,
                top_k,
                top_p,
                repetition_penalty,
                no_repeat_ngram_size=no_repeat_ngram_size,
                repetition_window=repetition_window,
            )
            generated = torch.cat([generated, next_token], dim=1)
            yield next_token
            if (
                step >= min_new_tokens
                and stops
                and all(int(t) in stops for t in next_token.view(-1).tolist())
            ):
                break
            out = self.forward(
                next_token,
                caches=caches,
                use_cache=True,
                encoder_hidden_states=encoder_hidden_states,
            )
            caches = out["caches"]
            logits = out["logits"][:, -1, :]

    @torch.no_grad()
    def generate_batch(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        eos_token_id: int | None = None,
        pad_token_id: int = 0,
        no_repeat_ngram_size: int = 3,
    ) -> torch.Tensor:
        """Left-pad aware batch generation (simple shared-length path)."""
        del attention_mask  # reserved for future packing-aware decode
        del pad_token_id
        return self.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            eos_token_id=eos_token_id,
            no_repeat_ngram_size=no_repeat_ngram_size,
        )

    def exact_parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def trainable_parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
