from __future__ import annotations

from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json


@dataclass(slots=True)
class ModelConfig:
    vocab_size: int = 512
    max_seq_len: int = 512
    n_layers: int = 6
    n_heads: int = 8
    n_kv_heads: int | None = None
    d_model: int = 512
    d_ff: int = 1365
    rope_theta: float = 10000.0
    dropout: float = 0.0
    bias: bool = False
    tie_embeddings: bool = True
    cross_attention: bool = False
    use_rmsnorm: bool = True
    gradient_checkpointing: bool = False
    rope_scaling: float = 1.0
    initializer_range: float = 0.02

    def __post_init__(self) -> None:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        if self.n_kv_heads is None:
            self.n_kv_heads = self.n_heads
        if self.n_heads % self.n_kv_heads != 0:
            raise ValueError("n_heads must be divisible by n_kv_heads")
        if self.max_seq_len < 2:
            raise ValueError("max_seq_len must be >= 2")

    @classmethod
    def from_json(cls, path: str | Path) -> "ModelConfig":
        raw = json.loads(Path(path).read_text())
        allowed = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in allowed})

    def to_json(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(asdict(self), indent=2))

    def to_dict(self) -> dict:
        return asdict(self)

    def parameter_estimate(self) -> int:
        head_dim = self.d_model // self.n_heads
        kv_dim = (self.n_kv_heads or self.n_heads) * head_dim
        attn_per_layer = (
            self.d_model * self.d_model
            + self.d_model * kv_dim
            + self.d_model * kv_dim
            + self.d_model * self.d_model
        )
        if self.cross_attention:
            attn_per_layer *= 2
        ff_per_layer = 3 * self.d_model * self.d_ff
        norms = self.n_layers * (3 if self.cross_attention else 2) * self.d_model
        embed = self.vocab_size * self.d_model
        lm_head = 0 if self.tie_embeddings else embed
        return self.n_layers * (attn_per_layer + ff_per_layer) + norms + embed + lm_head
