# Training OM-70B (architecture preset)

Config: `configs/70b.json`.

## Architecture (software only)

- `d_model=8192`, `n_layers=80`, `n_heads=64`, `n_kv_heads=8` (GQA)
- `d_ff=28672`, `max_seq_len=8192`, `vocab_size=65536`
- `gradient_checkpointing: true`

```bash
om-ai model-info --config configs/70b.json
```

This describes a **~70B-class** dense decoder layout for `OMTransformer`. It is not a finished model.

## Critical honesty statement

**Trained OM-70B weights require real large-scale training.**

This repository does **not** contain:

- Pretrained 70B parameters
- A hidden “already trained” checkpoint renamed as 70B
- Benchmark scores implying frontier capability

Shipping architecture + trainers is not the same as shipping learned knowledge. Learned knowledge lives in weights produced by:

1. A legally usable, high-quality corpus at massive token scale
2. A tokenizer fitted to that corpus
3. A GPU/accelerator fleet sized for 70B training (multi-node FSDP/ZeRO, weeks–months of wall time is typical in industry)
4. Pretraining, then SFT/alignment, then rigorous evaluation and red-teaming
5. Artifact integrity, registry promotion, and continuous monitoring

Until those runs complete and pass your gates, treat any 70B instantiation as **untrained or under-trained parameters**, not an operating brain.

## Software you can use when ready

- Model: `om_ai/model/transformer.py`
- Distributed: `om_ai/training/distributed.py` (FSDP), `om_ai/training/deepspeed_train.py`
- Post-train: `sft.py`, `reward_model.py`, `dpo.py`, `ppo.py`
- Packaging: `om_ai/checkpoint/`, `om_ai/registry/`

## Promotion rule

Never set production/`trained=True` for a 70B artifact without measured evals on held-out suites you own or license. See `EXTERNAL_ASSETS_REQUIRED.md` and `BENCHMARKS.md`.
