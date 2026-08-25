# OM AI Genesis Platform v1.0 — System Architecture

**Status:** Master specification mapped onto this repository.  
**Models:** OM-1.0 (foundation) → OM-7.0 (advanced) → OM-70.0 (large-scale) — shapes + training path; weights require compute + licensed data.

## Vision

Traditional: `User → Prompt → LLM → Answer`  

OM AI: Human → Experience Layer → Cognitive OS → (Intelligence Core, Reasoning, Planning, Memory, Knowledge, Agents, Tools, Multimodal, Hardware, Robotics, Research) → Real-world systems.

The LLM is the **core brain**, not the whole product.

## Map to this repo

| Spec area | Repository location |
|---|---|
| Core / intent / reasoning | `om_ai/understanding/`, `om_ai/agent/`, `om_ai/runtime/` |
| Memory | `om_ai` memory APIs + chat memory flags |
| Knowledge / RAG | `om_ai/knowledge/`, **`om_ai/knowledge_brain/`** |
| Agents / tools | `om_ai/agent/` |
| Response intelligence | `om_ai/response_engine/` |
| Training | `om_ai/training/`, `om_ai/data_pipeline/` |
| Multimodal | `om_ai/multimodal/`, `om_ai/vision/` |
| Hardware / robotics | `om_ai/operating_intelligence/embodiment/` |
| Genesis / JARVIS | `om_ai/genesis/`, `docs/PROJECT_GENESIS_JARVIS.md` |
| API / frontend | `om_ai/api/`, `om_ai/api/static/chat.html` |
| Security | `om_ai/security/` |

## Version strategy

| Model | Role |
|---|---|
| **OM-1.0** | Foundation: conversation, coding, reasoning, docs, agents, memory, tools |
| **OM-7.0** | Professional: deeper reasoning, larger context, complex design |
| **OM-70.0** | Large-scale: scientific depth, enterprise, complex agents |

## Knowledge Brain (1600–2026)

See **[`OM_KNOWLEDGE_BRAIN_1600_2026.md`](OM_KNOWLEDGE_BRAIN_1600_2026.md)** and package `om_ai/knowledge_brain/`.

Honest rule: **prompt ≠ weights**. Path = corpus + RAG + SFT + scale.

## Roadmap phases

1. **OM-1.0** — core, memory, agents, coding, knowledge, response engine  
2. **OM-1.0 Advanced** — vision, voice, automation, richer tools  
3. **OM-7.0** — advanced reasoning, large context, enterprise  
4. **OM-70.0** — large model + scientific / autonomous agents  

## Commands

```bash
om-ai knowledge-brain catalog
om-ai knowledge-brain init
om-ai knowledge-brain generate --count 2000
om-ai genesis generate --count 5000
om-ai sft --checkpoint artifacts/checkpoints/omai-20m-base/latest.pt \
  --data data/om-knowledge-brain-v1/train/om_knowledge_instruct_v1.jsonl \
  --output artifacts/checkpoints/om-1.0-knowledge-sft
```

Related: [`PROJECT_GENESIS_JARVIS.md`](PROJECT_GENESIS_JARVIS.md), [`OM10_GENESIS_CORPUS_SPEC.md`](OM10_GENESIS_CORPUS_SPEC.md), [`OWN_INTELLIGENCE_ROADMAP.md`](OWN_INTELLIGENCE_ROADMAP.md).
