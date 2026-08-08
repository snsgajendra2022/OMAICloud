# Quick Start — OM AI v0.3

## Install

```bash
cd "/path/to/om-ai-operating-brain"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
```

Requires Python ≥ 3.11 and PyTorch ≥ 2.4.

## Tiny CPU smoke path

```bash
om-ai tokenizer train \
  --input data/example_corpus.txt \
  --output artifacts/tokenizer.json \
  --vocab-size 512

om-ai train \
  --config configs/tiny.json \
  --data data/example_corpus.txt \
  --tokenizer artifacts/tokenizer.json \
  --steps 20

om-ai generate \
  --config configs/tiny.json \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/checkpoints/latest.pt \
  --prompt "OM AI"
```

Or one-shot pipeline:

```bash
python scripts/run_actual_training_pipeline.py --steps 5
```

## API

```bash
om-ai serve --host 127.0.0.1 --port 8080
# Open http://127.0.0.1:8080/docs
```

Auth: set API keys via env (see `.env.example` and `om_ai/security/auth.py`). Do not expose publicly without TLS and hardened allowlists.

## Useful CLI commands

| Command | Purpose |
|---------|---------|
| `om-ai model-info --config …` | Parameter estimate |
| `om-ai tokenizer {train,inspect,encode,decode}` | Tokenizer ops |
| `om-ai corpus {import,validate,dedupe,audit,shard,stats}` | Corpus governance |
| `om-ai pretrain` / `om-ai train` | Causal LM pretraining |
| `om-ai sft` / `om-ai reward` / `om-ai dpo` | Post-training |
| `om-ai evaluate` / `om-ai benchmark` | Local eval |
| `om-ai generate` / `om-ai chat` | Inference |
| `om-ai feedback {add,export}` | Continuous learning I/O |
| `om-ai registry {list,register}` | Model registry |
| `om-ai bundle` | Checkpoint bundle + integrity |
| `om-ai project-scan` | Local project discovery |
| `om-ai serve` | FastAPI server |

## Tests

```bash
pytest -q
# or: make test
```

## Expectation

Tiny checkpoints prove code trains real tensors. They are **not** capable language models. Scale presets need your corpus and GPUs — see `TRAINING.md` and `EXTERNAL_ASSETS_REQUIRED.md`.
