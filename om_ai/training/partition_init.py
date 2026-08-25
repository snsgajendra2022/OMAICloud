"""Partition-aware model construction for 70B-scale training.

Problem with the old DeepSpeed entrypoint:
    model = OMTransformer(cfg)   # materializes *full* 70B on one process
    deepspeed.initialize(...)    # partitions only *after* OOM

This module builds the model under ZeRO-3 Init or on the meta device so a
single GPU never has to hold the full parameter set first.
"""
from __future__ import annotations

from typing import Any, Callable, Literal

import torch
import torch.nn as nn

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer

InitStrategy = Literal["eager", "meta", "deepspeed_zero3"]


def _reinit_weights(model: OMTransformer) -> None:
    model.apply(model._init_weights)


def create_om_transformer(
    cfg: ModelConfig,
    *,
    strategy: InitStrategy = "eager",
    deepspeed_config: dict[str, Any] | str | None = None,
    dtype: torch.dtype | None = torch.bfloat16,
) -> OMTransformer:
    """Construct OMTransformer with the requested memory strategy.

    - eager: normal ``__init__`` (tiny / single-GPU only)
    - meta: tensors on ``meta`` device (caller must materialize under FSDP)
    - deepspeed_zero3: ``deepspeed.zero.Init`` so params are partitioned at creation
    """
    if strategy == "eager":
        return OMTransformer(cfg)

    if strategy == "meta":
        with torch.device("meta"):
            return OMTransformer(cfg, skip_init=True)

    if strategy == "deepspeed_zero3":
        try:
            import deepspeed
            from deepspeed.runtime.zero import Init as ZeroInit
        except ImportError as exc:
            raise RuntimeError(
                "DeepSpeed is required for strategy=deepspeed_zero3. "
                "Install with: pip install -e '.[deepSpeed]'"
            ) from exc

        init_kwargs: dict[str, Any] = {"dtype": dtype or torch.bfloat16}
        if deepspeed_config is not None:
            # DeepSpeed accepts config path or dict depending on version.
            init_kwargs["config_dict_or_path"] = deepspeed_config
        with ZeroInit(**init_kwargs):
            model = OMTransformer(cfg)
        return model

    raise ValueError(f"unknown strategy: {strategy}")


def fsdp_param_init_fn(device: torch.device) -> Callable[[nn.Module], None]:
    """Materialize meta modules onto ``device`` and apply OM weight init."""

    def _init(module: nn.Module) -> None:
        module.to_empty(device=device, recurse=False)
        if isinstance(module, OMTransformer):
            _reinit_weights(module)
        elif isinstance(module, (nn.Linear, nn.Embedding)):
            # Leaf modules materialized by FSDP wrap; parent OMTransformer
            # apply may not run — init common leaf types here.
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    return _init


def wrap_fsdp(model: OMTransformer, *, local_rank: int, use_meta: bool = True):
    """Wrap model in FSDP, optionally materializing from meta tensors."""
    from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
    from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy
    import functools

    from om_ai.model.transformer import TransformerBlock

    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")
    policy = functools.partial(
        transformer_auto_wrap_policy,
        transformer_layer_cls={TransformerBlock},
    )
    kwargs: dict[str, Any] = {
        "auto_wrap_policy": policy,
    }
    if torch.cuda.is_available():
        kwargs["device_id"] = local_rank
    if use_meta:
        kwargs["param_init_fn"] = fsdp_param_init_fn(device)
        kwargs["sync_module_states"] = True
    return FSDP(model, **kwargs)


def recommended_strategy(param_estimate: int, *, prefer_deepspeed: bool = True) -> InitStrategy:
    """Heuristic: >3B params should not use eager single-process materialization."""
    if param_estimate < 3_000_000_000:
        return "eager"
    if prefer_deepspeed:
        # Prefer find_spec — importing deepspeed can abort on mismatched CUDA builds.
        import importlib.util

        if importlib.util.find_spec("deepspeed") is not None:
            return "deepspeed_zero3"
        return "meta"
    return "meta"
