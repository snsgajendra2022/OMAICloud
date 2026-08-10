# Supervised Fine-Tuning (SFT)

Module: `om_ai/training/sft.py` — CLI: `om-ai sft`.

## Format

JSONL rows:

```json
{"system":"optional","prompt":"user request","response":"assistant answer"}
```

Example: `data/example_sft.jsonl`.

## Behavior

`SFTTrainer` / `SFTDataset` use `tokenizer.encode_chat` (same special-token IDs as inference):

- training: `<bos>…<user>…</user><assistant>answer</assistant><eos>`
- inference prompt: same prefix ending at opening `<assistant>` (`add_generation_prompt=True`)

Prompt tokens through the opening `<assistant>` are label-masked; loss is on the assistant span only. The tokenizer must include chat specials (`<system>`, `<user>`, `<assistant>`) — do not SFT with the legacy demo vocab that only has pad/bos/eos/unk.

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
