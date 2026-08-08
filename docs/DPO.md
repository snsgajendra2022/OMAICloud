# Direct Preference Optimization (DPO)

Module: `om_ai/training/dpo.py` — CLI: `om-ai dpo`.

## Format

```json
{"prompt":"…","chosen":"preferred answer","rejected":"worse answer"}
```

Example: `data/example_preferences.jsonl`. Dataset class: `PreferenceDataset` in `om_ai/training/preference.py`.

## Behavior

`DPOTrainer` trains the policy against a **frozen reference** copy using the standard DPO objective (beta-controlled). No separate reward model is required for DPO itself (contrast with RLHF reward + PPO path).

## Run

```bash
om-ai dpo \
  --config configs/tiny.json \
  --data data/example_preferences.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/sft/latest.pt \
  --steps 500 \
  --beta 0.1 \
  --lr 1e-6 \
  --output artifacts/dpo
```

Typical sequence: pretrain → SFT → DPO. The demo artifact `artifacts/demo/om-tiny-dpo.pt` was produced this way on toy data.

## Honesty

DPO improves preference alignment **relative to the base checkpoint**. It cannot inject world knowledge missing from pretraining. Large preference corpora are external — not fabricated by this repo.
