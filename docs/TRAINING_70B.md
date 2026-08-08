# Training OM-70B (architecture + launcher)

Config: `configs/70b.json`. Launcher: `om-ai train-70b`.

## Architecture (software only)

- `d_model=8192`, `n_layers=80`, `n_heads=64`, `n_kv_heads=8` (GQA)
- `d_ff=28672`, `max_seq_len=8192`, `vocab_size=65536`
- `gradient_checkpointing: true`

```bash
om-ai model-info --config configs/70b.json
```

This describes a **~70B-class** dense decoder layout for `OMTransformer`. It is not a finished model.

## Launcher (deliberate — not started by `serve`)

```bash
om-ai train-70b \
  --data /data/om-corpus \
  --tokenizer /data/tokenizer.json \
  --output /checkpoints/om-70b
```

What it does:

1. Validate corpus presence / optional license manifest
2. Validate tokenizer
3. Check CUDA GPUs, count, VRAM
4. Check distributed env hints + disk space
5. Load `configs/70b.json`
6. Start DeepSpeed ZeRO-3 (default) or FSDP with **partition-aware init**
7. Save resumable checkpoints + `OM70B_TRAINING_STATUS.json`
8. Optional SFT / preference / benchmarks when you pass those flags
9. Only mark `trained` / production candidate after **benchmark gates** (`configs/train_70b_gates.json`)

Preflight only (safe on a Mac):

```bash
om-ai train-70b \
  --data data/example_corpus.txt \
  --tokenizer artifacts/demo/tokenizer.json \
  --output artifacts/om70b_preflight \
  --preflight-only \
  --min-gpus 1 \
  --min-vram-gb 1 \
  --min-free-gb 1 \
  --min-corpus-bytes 10
```

On a Mac without CUDA this correctly reports **not ready** for final 70B pretraining.

### Partition-aware init

Legacy DeepSpeed entry built the full model first (`OMTransformer(cfg)`), then partitioned — that OOMs at 70B.

Fixed path: `om_ai/training/partition_init.py`

- ZeRO-3: `deepspeed.zero.Init` while constructing the model
- FSDP: meta-device construction + `param_init_fn` materialization

### `om-ai serve` will not train 70B

`OM_AI_AUTO_TRAIN_70B=1` is **ignored** by serve (warning only). Use `train-70b` on a dedicated GPU deployment.

## Critical honesty statement

**Trained OM-70B weights require real large-scale training.**

This repository does **not** contain pretrained 70B parameters, hidden “already trained” checkpoints, or frontier benchmark claims.

Learned knowledge requires:

1. Licensed high-quality corpus at massive token scale
2. Tokenizer fitted to that corpus
3. GPU/accelerator fleet (multi-node FSDP/ZeRO; weeks–months typical)
4. Pretrain → SFT/alignment → eval / red-team
5. Artifact integrity + registry promotion

Until those runs complete and pass your gates, treat any 70B instantiation as **untrained or under-trained parameters**, not an operating brain.

### Status machine

```
NOT_STARTED → PREFLIGHT → PRETRAIN → PRETRAINED
    → SFT → ALIGNED → BENCHMARKED → PRODUCTION_CANDIDATE
```

Mac / GitHub can ship software. Final weights come from the GPU cluster.

## Software map

| Piece | Path |
|-------|------|
| Launcher | `om_ai/training/train_70b.py` |
| Preflight | `om_ai/training/preflight.py` |
| Partition init | `om_ai/training/partition_init.py` |
| DeepSpeed | `om_ai/training/deepspeed_train.py` |
| FSDP | `om_ai/training/distributed.py` |
| Gates | `configs/train_70b_gates.json` |

## Promotion rule

Never set production / `trained=True` for a 70B artifact without measured evals on held-out suites you own or license. Never claim GPT-equivalent capability without evidence. See `EXTERNAL_ASSETS_REQUIRED.md` and `BENCHMARKS.md`.
