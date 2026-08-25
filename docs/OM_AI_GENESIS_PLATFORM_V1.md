# OM AI Genesis Platform v1.0 — System Architecture

**Status:** Production foundation **implemented** (software layers verified).  
**Report:** `artifacts/GENESIS_PLATFORM_REPORT.json` · `om-ai system build` → **45/45**  
**Models:** OM-1.0 (foundation) → OM-7.0 → OM-70.0 — shapes + training path; weights need GPU + licensed data.

**Cursor execution master prompt:**  
[`docs/prompts/OM_AI_GENESIS_PLATFORM_PRODUCTION_MASTER_PROMPT.md`](prompts/OM_AI_GENESIS_PLATFORM_PRODUCTION_MASTER_PROMPT.md)

## EXISTING vs IMPLEMENTED (2026-08-25)

| Layer | Status | Location |
|---|---|---|
| 1 Intelligence Core | ✅ | `om_ai/core/intent_engine/`, `core/response/`, `core/reasoning/` |
| 2 Reasoning Engine | ✅ | `om_ai/core/reasoning/` + `om_ai/reasoning/` |
| 3 Knowledge Brain | ✅ | `knowledge/`, `knowledge_brain/`, `knowledge_universe/`, `knowledge/corpus.py` |
| 4 Memory System | ✅ | `om_ai/memory/layers.py` (short/conversation/user/project/experience/skill) |
| 5 Agent System | ✅ | `om_ai/agents/roles.py` + orchestrator |
| 6 Tool System | ✅ | `om_ai/tools/` |
| 7 Coding Intelligence | ✅ | `om_ai/coding_brain/` + coding agent |
| 8 Multimodal | 🟡 | Document AI ready; vision/voice stubs (`multimodal/*`) |
| 9 Evaluation | ✅ | `om_ai/evaluation/` + benchmarks |
| 10 Continuous Learning | ✅ | `om_ai/learning/` + continuous |
| 11 Training Pipeline | ✅ | `om_ai/training/`, `configs/`, `training/` |
| 12 Security | ✅ | `om_ai/security/` |
| 13 Enterprise | ✅ | `om_ai/enterprise/` + tenancy |

**External only:** OM-1B/7B/70B weights · massive licensed corpora · GPU time · trained vision/ASR/TTS.

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
om-ai system build
om-ai intent classify "Create React login page"
om-ai reason "Create React login page"
om-ai knowledge status
om-ai evaluate run
om-ai continuous export
om-ai knowledge-brain catalog
om-ai knowledge-brain generate --count 2000
```

Related: [`PROJECT_GENESIS_JARVIS.md`](PROJECT_GENESIS_JARVIS.md), [`OM10_GENESIS_CORPUS_SPEC.md`](OM10_GENESIS_CORPUS_SPEC.md), [`OWN_INTELLIGENCE_ROADMAP.md`](OWN_INTELLIGENCE_ROADMAP.md).
