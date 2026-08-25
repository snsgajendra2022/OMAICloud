# OM-1.0 Genesis Training (quick how-to)

**Full corpus constitution:** [`OM10_GENESIS_CORPUS_SPEC.md`](OM10_GENESIS_CORPUS_SPEC.md)  
**Vision blueprint:** [`PROJECT_GENESIS_JARVIS.md`](PROJECT_GENESIS_JARVIS.md)

A system prompt does **not** train the model. Use the corpus + SFT.

```bash
om-ai genesis domains
om-ai genesis generate --count 1000 \
  --out data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl

om-ai sft \
  --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/omai-20m-base/latest.pt \
  --data data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl \
  --output artifacts/checkpoints/omai-20m-genesis-sft \
  --steps 500 --device mps
```

Package: `om_ai/genesis/` · Data: `data/omai-genesis-v1/`
