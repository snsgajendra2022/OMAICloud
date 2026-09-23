# Architecture — OM AI Operating Brain v0.3

OM AI is a self-hosted **cognitive operating system**: model code, training, agents, memory, RAG, and API run locally. It does **not** call OpenAI/Anthropic/Google model APIs and does not include ChatGPT weights or private OpenAI training data.

Operating-system pillars, gaps, and roadmap:

- [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md) — **full structure + production runtime map**
- [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md)
- [SYSTEM_GAP_ANALYSIS.md](SYSTEM_GAP_ANALYSIS.md)
- [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)
- [OM_OPERATING_SYSTEM.md](OM_OPERATING_SYSTEM.md)

## Layers

```text
CLI / FastAPI (om_ai/cli.py, om_ai/api/)
        │
AgentOrchestrator (om_ai/agents/) ← tools, planner, audit
        │
Runtime LocalLLMEngine (om_ai/runtime/)
        │
OMTransformer (om_ai/model/) + ByteBPETokenizer (om_ai/tokenizer/)
        │
Memory │ RAG │ Registry │ Corpus │ Security │ Integrations
```

## Core modules

| Area | Package | Role |
|------|---------|------|
| Model | `om_ai/model/` | Decoder-only Transformer: RoPE, GQA/MHA, RMSNorm/LayerNorm, SwiGLU, KV cache, optional cross-attention |
| Config | `om_ai/core/config.py` | `ModelConfig` + JSON presets under `configs/` |
| Tokenizer | `om_ai/tokenizer/` | Byte-level BPE |
| Training | `om_ai/training/` | Pretrain, SFT, reward, DPO, PPO infra, DDP/FSDP, DeepSpeed entry |
| Corpus | `om_ai/corpus/`, `om_ai/data/` | Import, license gates, PII scrub, dedupe, shard, dataset pipeline |
| Runtime | `om_ai/runtime/` | Local load + generate/chat |
| Agents | `om_ai/agents/`, `om_ai/reasoning/`, `om_ai/actions/` | Plan → tools → verify; shell/knowledge tools |
| Memory | `om_ai/memory/` | Tenant-isolated SQLite multi-kind store |
| RAG | `om_ai/knowledge/` | Persistent lexical/TF-IDF retrieval (no external embed API required) |
| Vision/Speech | `om_ai/vision/`, `om_ai/voice/`, `om_ai/multimodal/` | Trainable encoders + request router |
| Security | `om_ai/security/` | API keys, RBAC, SSRF, audit, rate limits, secrets |
| Registry | `om_ai/registry/`, `om_ai/checkpoint/` | Lifecycle metadata + integrity bundles |
| Eval | `om_ai/eval/` | Smoke harness + JSONL benchmark runner |
| Continuous | `om_ai/continuous/` | Feedback store + SFT/preference replay export |

## Honest boundary

Architecture presets (`configs/1b.json` … `70b.json`) define **shapes**, not trained intelligence. Useful capability appears only after licensed data + real GPU training produce weights. The repo ships a tiny demo checkpoint under `artifacts/demo/` as pipeline proof only.
