"""ChatGPT-parity upgrade roadmap for OM-1.0 (sampling → architecture → SFT → DPO).

OM already ships RoPE + RMSNorm + SwiGLU + SDPA. This module audits readiness
and documents the training path:

  [Pre-trained Base OM]
         │
         ▼
  [1. SFT: Supervised Fine-Tuning]  → chat tags via tokenizer.encode_chat
         │
         ▼
  [2. DPO Alignment]                → PreferenceDataset + DPOTrainer
"""
from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ArchitectureAudit:
    rope: bool
    rmsnorm: bool
    swiglu: bool
    scaled_dot_product_attention: bool
    temperature_top_p_repetition: bool
    no_repeat_ngram: bool
    sft_trainer: bool
    dpo_trainer: bool
    chat_specials: bool
    notes: list[str]

    @property
    def phase1_ok(self) -> bool:
        return self.temperature_top_p_repetition and self.no_repeat_ngram

    @property
    def phase2_ok(self) -> bool:
        return self.rope and self.rmsnorm and self.swiglu and self.scaled_dot_product_attention

    @property
    def phase3_ok(self) -> bool:
        return self.sft_trainer and self.dpo_trainer and self.chat_specials

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase1_ok"] = self.phase1_ok
        d["phase2_ok"] = self.phase2_ok
        d["phase3_ok"] = self.phase3_ok
        d["chatgpt_parity_ready"] = self.phase1_ok and self.phase2_ok and self.phase3_ok
        return d


def audit_chatgpt_parity(*, tokenizer: Any | None = None) -> ArchitectureAudit:
    """Verify OM-1.0 has the four-stage ChatGPT upgrade pieces in code."""
    notes: list[str] = []
    from om_ai.model import transformer as tr
    from om_ai.model.rope import apply_rope, precompute_rope
    from om_ai.core.config import ModelConfig

    cfg = ModelConfig()
    rope = callable(apply_rope) and callable(precompute_rope) and cfg.rope_theta > 0
    rmsnorm = bool(cfg.use_rmsnorm) and hasattr(tr, "RMSNorm")
    swiglu = hasattr(tr, "SwiGLU")
    sdpa = "scaled_dot_product_attention" in inspect.getsource(tr.CausalSelfAttention.forward)
    gen_sig = inspect.signature(tr.OMTransformer.generate)
    params = gen_sig.parameters
    sampling = all(k in params for k in ("temperature", "top_p", "repetition_penalty"))
    ngram = "no_repeat_ngram_size" in params

    from om_ai.training.sft import SFTTrainer
    from om_ai.training.dpo import DPOTrainer

    chat_ok = True
    if tokenizer is not None:
        inspect_fn = getattr(tokenizer, "inspect", None)
        if callable(inspect_fn):
            chat_ok = bool(inspect_fn().get("chat_tokens_available"))
            if not chat_ok:
                notes.append(
                    "Tokenizer missing chat specials (<system>/<user>/<assistant>). "
                    "Train/save a chat-capable tokenizer before SFT."
                )
        else:
            chat_ok = False
            notes.append("Tokenizer has no inspect(); cannot verify chat specials.")
    else:
        notes.append(
            "Pass tokenizer=... to verify chat specials. OM uses "
            "<system>…</system><user>…</user><assistant>…</assistant> "
            "(ChatML-equivalent; not <|im_start|>)."
        )

    if not notes:
        notes.append("Architecture + sampling + SFT/DPO trainers present in-tree.")
    notes.append(
        "Quality still depends on dense conversational SFT/DPO data and a trained checkpoint — "
        "code readiness ≠ ChatGPT fluent weights."
    )

    return ArchitectureAudit(
        rope=rope,
        rmsnorm=rmsnorm,
        swiglu=swiglu,
        scaled_dot_product_attention=sdpa,
        temperature_top_p_repetition=sampling,
        no_repeat_ngram=ngram,
        sft_trainer=SFTTrainer is not None,
        dpo_trainer=DPOTrainer is not None,
        chat_specials=chat_ok,
        notes=notes,
    )


def recommended_cli_commands(
    *,
    sft_jsonl: str = "data/sft/chat_conversations.jsonl",
    dpo_jsonl: str = "data/dpo/preferences.jsonl",
    config: str = "configs/om-1.0-local.json",
    tokenizer: str = "artifacts/tokenizer-fixed-v3.json",
    checkpoint: str = "artifacts/checkpoints/om-1.0-long/latest.pt",
) -> list[str]:
    """Concrete next commands after Phase 1–2 code is green."""
    return [
        (
            f"om-ai sft --config {config} --tokenizer {tokenizer} "
            f"--data {sft_jsonl} --checkpoint {checkpoint} --output artifacts/sft"
        ),
        (
            f"om-ai dpo --config {config} --tokenizer {tokenizer} "
            f"--data {dpo_jsonl} --checkpoint artifacts/sft/latest.pt "
            f"--output artifacts/dpo --beta 0.1"
        ),
        "export OM_MODEL_CHECKPOINT=artifacts/dpo/latest.pt",
        "om-ai serve",
    ]


def write_example_datasets(root: str | Path) -> dict[str, str]:
    """Write tiny SFT + DPO JSONL templates for the ChatGPT training path."""
    root = Path(root)
    sft_path = root / "data" / "sft" / "chat_conversations.example.jsonl"
    dpo_path = root / "data" / "dpo" / "preferences.example.jsonl"
    sft_path.parent.mkdir(parents=True, exist_ok=True)
    dpo_path.parent.mkdir(parents=True, exist_ok=True)

    sft_rows = [
        {
            "messages": [
                {"role": "system", "content": "You are OM AI, a helpful assistant."},
                {"role": "user", "content": "What is 15% of 200?"},
                {"role": "assistant", "content": "15% of 200 is 30."},
            ]
        },
        {
            "system": "You are OM AI, a helpful assistant.",
            "prompt": "Say hello briefly.",
            "response": "Hello! How can I help you today?",
        },
    ]
    dpo_rows = [
        {
            "system": "You are OM AI, a helpful assistant.",
            "prompt": "Explain gravity in one sentence.",
            "chosen": "Gravity is the attractive force between masses that keeps planets in orbit and objects on Earth grounded.",
            "rejected": "allows allows allows gravity gravity gravity the the the",
        },
        {
            "prompt": "What is today's date used for?",
            "chosen": "People ask for today's date to schedule events, log work, or confirm calendars.",
            "rejected": "date date date date allows allows",
        },
    ]
    sft_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in sft_rows) + "\n",
        encoding="utf-8",
    )
    dpo_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in dpo_rows) + "\n",
        encoding="utf-8",
    )
    return {"sft_example": str(sft_path), "dpo_example": str(dpo_path)}
