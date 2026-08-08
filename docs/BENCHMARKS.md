# Benchmarks

Modules: `om_ai/eval/benchmarks.py`, `om_ai/eval/runner.py` — CLI: `om-ai evaluate`, `om-ai benchmark`.

## Included harness

- Smoke suite: language / reasoning / math / coding / tool-use **prompt completions** (qualitative)
- Perplexity helper on short texts
- JSONL runner: `benchmarks/core.jsonl` → report under `artifacts/eval/`

Example cases use simple `contains` metrics (e.g. math `2+2`, coding expects `def`). These validate the **pipeline**, not frontier ability.

## Run

```bash
om-ai evaluate \
  --config configs/tiny.json \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/demo/om-tiny-dpo.pt

om-ai benchmark \
  --config configs/tiny.json \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/demo/om-tiny-dpo.pt \
  --benchmark benchmarks/core.jsonl \
  --report artifacts/eval/report.json
```

## Honest status

- **No invented MMLU / HumanEval / LMSYS scores** are published here
- Demo/tiny acceptance results are expected to be **below useful capability**
- Large public suites: harness can be pointed at licensed/local copies; datasets themselves are **external**

Record real numbers in registry metadata only after you run them.
