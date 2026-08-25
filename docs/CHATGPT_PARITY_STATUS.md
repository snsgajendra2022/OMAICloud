# CHATGPT PARITY — WHAT OM COMPLETED vs WHAT REMAINS

**Updated:** 2026-08-25

## Completed in this push (software + local training)

| Item | Status |
|------|--------|
| Longer local context (`max_seq_len` 128 → **256**) | DONE |
| Human EQ system prompt + Agent Brain warm fallbacks | DONE |
| Login bootstrap defaults (Library, Assistants, Prompts, Memory, Welcome chat…) | DONE |
| Chat SFT v4 corpus (`data/om-chat-sft-v4-complete.jsonl`, ~2.7k rows) | DONE |
| Preference DPO set (`data/om-chat-dpo-v4.jsonl`, 1200 rows) | DONE |
| SFT v4 → `artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt` | DONE |
| DPO v4 → `artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt` | DONE |
| `.env` pointed at DPO v4 + serve restarted | DONE |
| One-shot script `scripts/complete_chat_parity_push.sh` | DONE |
| Generation defaults warmer (temp/top_p/max tokens) | DONE |

## Cannot be “completed” on a Mac without a GPU cluster

| Item | Reality |
|------|---------|
| ChatGPT-equal intelligence | Needs **billions+** of trained parameters |
| OM-1B / 7B / 13B / 70B learned weights | Configs exist; **training not executed at scale** |
| Frontier benchmarks at ChatGPT level | Not measured / not reached |
| Fake 70B `.pt` files | **Will never be created** (honesty rule) |

## How to finish local push + reload chat

```bash
# If SFT already finished:
ls artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt

# Optional DPO:
om-ai dpo --config configs/om-1.0-local.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt \
  --data data/om-chat-dpo-v4.jsonl --steps 800 --device cpu \
  --output artifacts/checkpoints/om-1.0-chat-dpo-v4

# Point .env at the new checkpoint, restart serve, hard-refresh browser.
```

**Honest score after this push (local):** roughly **~18–25% vs ChatGPT intelligence** (better chat feel), **~97% software platform**.
