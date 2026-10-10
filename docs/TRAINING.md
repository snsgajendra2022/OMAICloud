# Training Overview

OM AI separates **software** (trainers, configs, CLI) from **weights** (outputs of long GPU runs on licensed data).

## Stages

1. **Corpus** — `om_ai/corpus/`, `om_ai/data/`, scripts `prepare_corpus.py` / `shard_corpus.py`
2. **Tokenizer** — `om_ai/tokenizer/byte_bpe.py` via `om-ai tokenizer train`
3. **Pretrain** — `om_ai/training/trainer.py` via `om-ai train` / `om-ai pretrain`
4. **SFT** — `om_ai/training/sft.py` via `om-ai sft`
5. **Reward** — `om_ai/training/reward_model.py` via `om-ai reward`
6. **DPO** — `om_ai/training/dpo.py` via `om-ai dpo`
7. **PPO / RLHF infra** — `om_ai/training/ppo.py` (rollouts, GAE, clipped surrogate; needs policy + reward)
8. **Eval / registry** — `om_ai/eval/`, `om_ai/registry/`

Detailed production sequence: `TRAINING_RUNBOOK.md`.

## Single-process pretrain

```bash
om-ai train \
  --config configs/tiny.json \
  --data data/example_corpus.txt \
  --tokenizer artifacts/tokenizer.json \
  --steps 1000 \
  --batch-size 4 \
  --precision auto \
  --output artifacts/checkpoints
```

Features in `Trainer` (`om_ai/training/trainer.py`): AdamW, warmup/cosine, grad accum/clip, mixed precision, checkpoint resume.

## Distributed

See `DISTRIBUTED_TRAINING.md` — DDP/FSDP in `om_ai/training/distributed.py`, DeepSpeed in `om_ai/training/deepspeed_train.py`.

## Scale presets

| Config | Intent |
|--------|--------|
| `configs/tiny.json` | Dev / CI smoke |
| `configs/1b.json` | ~1B-class architecture |
| `configs/7b.json` | ~7B-class |
| `configs/13b.json` | ~13B-class |
| `configs/70b.json` | ~70B-class |

Use `om-ai model-info --config configs/7b.json` for estimates. Presets **do not** include trained weights.

## Apple Silicon local development\n\nFor an Apple M4 Mac with 48 GB or more unified memory, see [`MAC_M4_TRAINING.md`](MAC_M4_TRAINING.md) and the small-model profile [`configs/om-m4-48gb.json`](../configs/om-m4-48gb.json). Treat this as a pipeline-validation profile, not a frontier-quality model. For evidence-based capability milestones and benchmark gates, see [`OM_CLOUD_LEVEL_ROADMAP.md`](OM_CLOUD_LEVEL_ROADMAP.md).\n\n## What this repo has trained

- Demo: `artifacts/demo/om-tiny-dpo.pt` (tiny data, few steps)
- No OM-1B / 7B / 13B / 70B production weights are shipped

Capability requires your licensed tokens + cluster time. See scale-specific docs `TRAINING_1B.md` … `TRAINING_70B.md`.
