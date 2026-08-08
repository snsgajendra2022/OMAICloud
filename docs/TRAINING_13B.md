# Training OM-13B (architecture preset)

Config: `configs/13b.json`.

## Architecture (software)

- `d_model=5120`, `n_layers=40`, `n_heads=40`, `n_kv_heads=40`
- `d_ff=13824`, `max_seq_len=8192`, `vocab_size=65536`
- `gradient_checkpointing: true`

```bash
om-ai model-info --config configs/13b.json
```

## Honest status

**No OM-13B trained weights are in this ZIP.** The JSON + `OMTransformer` code let you instantiate and train the architecture. Frontier-like knowledge and tool use will not appear from short smoke runs.

## Compute posture

Treat 13B as a **cluster** job: FSDP or DeepSpeed ZeRO-3, high-bandwidth interconnect, durable checkpointing, and careful resume. Use the same data governance path (`om_ai/corpus/`, manifests) as smaller scales — license and contamination checks still apply.

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --strategy fsdp \
  --config configs/13b.json \
  --data /data/om_corpus.jsonl \
  --tokenizer artifacts/tokenizer.json
```

## After pretrain

1. Masked SFT (`om_ai/training/sft.py`)
2. Preference alignment (DPO and/or reward + PPO infra)
3. Benchmark + human review
4. Registry lifecycle: candidate → evaluated → approved → production (`om_ai/registry/`)

Do not mark `trained=True` / production unless weights and evals justify it.
