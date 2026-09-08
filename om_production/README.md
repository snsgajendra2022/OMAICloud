# OM Production Core (local ChatGPT-style SFT stack)

Folder layout matching the OM_Core checklist:

| File | Role |
|------|------|
| `dataset.txt` | Structured dialogues with `<|user|>` / `<|thought|>` / `<|final_response|>` |
| `tokenizer.py` | Custom BPE → `om_tokenizer.json` |
| `model.py` | Pre-LN + SwiGLU causal LM |
| `train.py` | AdamW + grad clip + checkpoints |
| `chat.py` | Interactive MPS/CPU chat loop |

## Launch on Mac

```bash
cd om_production
../.venv/bin/python build_dataset.py --rows 3000
../.venv/bin/python tokenizer.py
../.venv/bin/python train.py --steps 500   # use 2000+ for a longer run
../.venv/bin/python chat.py
```

## Recommended dataset size

| Goal | Rows in `dataset.txt` |
|------|------------------------|
| Smoke / learn the loop | 500–1,000 |
| Local Level-1 fluency start | **3,000–10,000** (default generator) |
| Serious chatbot quality | **50,000–500,000+** high-quality human/edited turns |

More rows help only if quality stays high (clear thought → final_response pairs).

## Multi-GPU note

Apple Silicon uses **one MPS device**, not CUDA multi-GPU. For CUDA clusters later, use `torchrun` + DDP around `train.py`; Mac training should stay single-process MPS.
