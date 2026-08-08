# Training OM-7B (architecture preset)

Config: `configs/7b.json`.

## Architecture (software)

- `d_model=4096`, `n_layers=32`, `n_heads=32`, `n_kv_heads=32`
- `d_ff=11008`, `max_seq_len=8192`, `vocab_size=65536`
- `gradient_checkpointing: true`

```bash
om-ai model-info --config configs/7b.json
```

## Honest status

**No trained OM-7B weights ship with this repository.** The preset is an architecture direction for `OMTransformer` (`om_ai/model/transformer.py`). Intelligence is not present until you run large-scale training.

Expect multi-GPU FSDP or DeepSpeed ZeRO for memory; single-GPU full fine-tune of a 7B dense model is usually impractical without heavy sharding/quantization (not a substitute for pretraining).

## Launch sketches

FSDP:

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --strategy fsdp \
  --config configs/7b.json \
  --data /data/om_corpus.jsonl \
  --tokenizer artifacts/tokenizer.json
```

DeepSpeed:

```bash
deepspeed --num_gpus 8 -m om_ai.training.deepspeed_train \
  --config configs/7b.json \
  --data /data/om_corpus.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --deepspeed configs/deepspeed_zero3.json
```

Post-train with `om-ai sft` / `om-ai reward` / `om-ai dpo` using matching config and checkpoints.

## External requirements

Licensed tokens, storage I/O for shards, checkpoint durability, and a real eval plan (`BENCHMARKS.md`). See `EXTERNAL_ASSETS_REQUIRED.md`.
