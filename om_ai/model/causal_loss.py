"""Causal language-modeling loss for OM chat / pretrain (assistant-only masking).

Labels use ``ignore_index=-100`` for padding and (in SFT) user/system prompt tokens
so gradients only flow through assistant completion tokens.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class OMCausalLoss(nn.Module):
    """Production causal cross-entropy with optional internal next-token shift.

    Two calling conventions (both supported):

    1. **Pre-shifted** (OM SFT collate / trainer): ``logits`` and ``labels`` already
       aligned for next-token prediction — no extra shift.
    2. **Full sequence**: same length as ``input_ids``; this module shifts so the
       model predicts the next token (ChatGPT-style training block).
    """

    def __init__(self, pad_token_id: int = -100, *, auto_shift: bool = False):
        super().__init__()
        self.ignore_index = int(pad_token_id)
        self.auto_shift = bool(auto_shift)
        self.loss_fn = nn.CrossEntropyLoss(ignore_index=self.ignore_index)

    def forward(
        self,
        logits: torch.Tensor,
        labels: torch.Tensor,
        *,
        shift: bool | None = None,
    ) -> torch.Tensor:
        # logits: (B, T, V)  labels: (B, T) or (B, T) full-seq when shift=True
        do_shift = self.auto_shift if shift is None else bool(shift)
        if do_shift:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
        else:
            # Pre-aligned (SFT collate already did ids[:-1] / labels[1:])
            shift_logits = logits.contiguous()
            shift_labels = labels.contiguous()
            if shift_logits.size(1) != shift_labels.size(1):
                # Recover if caller passed full-seq labels by mistake
                t = min(shift_logits.size(1), shift_labels.size(1))
                if logits.size(1) == labels.size(1) and logits.size(1) > 1:
                    shift_logits = logits[..., :-1, :].contiguous()
                    shift_labels = labels[..., 1:].contiguous()
                else:
                    shift_logits = shift_logits[:, :t, :]
                    shift_labels = shift_labels[:, :t]

        return self.loss_fn(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        )


def causal_cross_entropy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    *,
    ignore_index: int = -100,
    shift: bool = False,
) -> torch.Tensor:
    """Functional helper used by ``OMTransformer.forward``."""
    return OMCausalLoss(pad_token_id=ignore_index, auto_shift=shift)(
        logits, labels, shift=shift
    )


def build_assistant_only_labels(
    input_ids: list[int],
    *,
    prompt_len: int,
    pad_id: int = -100,
) -> list[int]:
    """Mask everything before the assistant completion (SFT / ChatML)."""
    labels = [pad_id] * min(prompt_len, len(input_ids))
    labels += input_ids[len(labels) :]
    return labels
