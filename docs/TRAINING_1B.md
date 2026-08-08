# Training OM-1B (architecture preset)

Config: `configs/1b.json` (also mirrored as `configs/om-1b.json` if present).

## Architecture (software)

Approximate shape from the JSON preset:

- `d_model=2048`, `n_layers=24`, `n_heads=16`, `n_kv_heads=8` (GQA)
- `d_ff=5504`, `max_seq_len=8192`, `vocab_size=65536` (override to match tokenizer)
- RMSNorm, RoPE (`rope_theta=500000`)

```bash
om-ai model-info --config configs/1b.json
```

## Honest status

**No trained OM-1B weights are included.** Instantiating the config creates random (or freshly initialized) parameters. Useful 1B behavior needs:

1. Large licensed corpus (order of tens–hundreds of billions of tokens is typical industry practice; choose your own budget)
2. Tokenizer trained on that corpus
3. Multi-GPU pretrain (DDP often enough at 1B)
4. SFT + preference/alignment data
5. Eval gates before registry `production`

## Suggested launch sketch

```bash
# After corpus + tokenizer are ready:
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --config configs/1b.json \
  --data /data/om_corpus.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --steps <your_budget> \
  --output artifacts/checkpoints/om-1b
```

Then SFT/DPO as in `SFT.md` / `DPO.md`, evaluate with `om-ai benchmark`, register with `om-ai registry register`.

## What “done” means

Done = measured eval on **your** held-out sets, not “config file exists.” Tiny demo checkpoints do not transfer to this scale.
