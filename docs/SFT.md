# Supervised Fine-Tuning (SFT)

Module: `om_ai/training/sft.py` — CLI: `om-ai sft`.

## Format

JSONL rows:

```json
{"system":"optional","prompt":"user request","response":"assistant answer"}
```

Example: `data/example_sft.jsonl`.

## Behavior

`SFTTrainer` / `SFTDataset` mask prompt (and system) tokens and optimize **response** tokens only (causal LM loss on assistant span).

## Run

```bash
om-ai sft \
  --config configs/tiny.json \
  --data data/example_sft.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/checkpoints/latest.pt \
  --steps 1000 \
  --batch-size 2 \
  --lr 2e-5 \
  --output artifacts/sft
```

Use the same architecture config as the base checkpoint. For scale presets, point `--checkpoint` at a **pretrained** weight file you actually trained — random init + SFT is not a substitute for pretraining.

## Data quality

SFT quality is dominated by instruction data, not CLI flags. Curate, dedupe, and license-check instruction corpora the same way as pretrain data (`om_ai/corpus/`, manifests).

## Continuous learning

High-rated production interactions can be exported via `om-ai feedback export` into SFT JSONL (`om_ai/continuous/replay.py`) for controlled fine-tunes — review before mixing into the main set.
