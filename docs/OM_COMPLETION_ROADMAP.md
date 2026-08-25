# OM Completion Roadmap — From Platform to AI Operating System

**Updated:** 2026-08-25  
**Honesty:** Software can be completed in-repo. **1B / 7B / 70B intelligence** needs licensed data + GPU time. This doc tracks both.

**Canonical ChatGPT gap analysis:** [`OM_CHATGPT_GAP_ANALYSIS.md`](OM_CHATGPT_GAP_ANALYSIS.md)  
**Rule:** OM needs the full intelligence stack around the model — not only bigger weights.

## Status board

| Layer | Status | Notes |
|---|---|---|
| Software platform | ✅ ~95–97% | API, train, agents, memory, security |
| UI/UX | ✅ ~70–85% | ChatGPT-like; keep polishing |
| Massive knowledge corpus | 🟡 scaffold → grow | `om-ai knowledge-universe init` |
| Reasoning engine | 🟡 → software DONE | `om_ai/reasoning/engine.py` |
| Coding agent | 🟡 contract + loop | `om_ai/agent/coding_agent.py` |
| Multi-agent collab | 🟡 present | Orchestrator + roles |
| Memory layers | 🟡 SQLite strong | Ranking/consolidation hooks |
| Multimodal | 🔴 weights EXTERNAL | ViT/ASR code exists |
| Evaluation platform | 🟡 → software DONE | `om-ai eval suite` |
| Continuous learning | 🟡 offline DONE | feedback → SFT/DPO JSONL |
| Alignment (DPO/RLHF) | 🟡 trainers exist | Need preference volume |
| Live knowledge | 🟡 gated | Enable network flags |
| Hardware/robotics | 🔴 stubs | Embodiment dry-run |
| Enterprise / scale | 🟡 partial | Multi-tenant API keys exist |
| Foundation 20M→1B→70B | 🔴 compute | Configs + train path only |

## The six must-complete gaps

1. **Large model weights** — train 100M → 1B → 7B → 70B on GPU  
2. **Huge quality dataset** — Knowledge Universe + licensed books/code/papers  
3. **Reasoning training** — engine + reasoning SFT/eval  
4. **Coding intelligence training** — coding agent + SWE-style eval  
5. **Evaluation system** — measure every checkpoint  
6. **Continuous learning** — feedback → dataset → fine-tune → new version  

## Phases

### Phase 1 — OM Brain Upgrade
`20M → 100M → 1B` strong language + coding on real tokens.

### Phase 2 — Knowledge Expansion
Fill `data/om-knowledge-universe-v1/` (books, papers, code, docs) + RAG embeddings.

### Phase 3 — Agent Intelligence
Coding/research/security agents with memory + tool selection.

### Phase 4 — OM-7
Professional assistant (7B-class + eval pass).

### Phase 5 — OM-70
Large-scale platform (70B-class + enterprise serving).

## Commands (software you can run now)

```bash
# Knowledge Universe folders
om-ai knowledge-universe init

# Reasoning demo (no GPU)
om-ai reason "Design a FastAPI auth service"

# Evaluation suite (heuristic + optional model)
om-ai eval suite --out artifacts/eval/latest.json

# Continuous learning export
om-ai continuous export --out data/continuous/

# Coding agent dry-run on this repo
om-ai coding plan --root . --task "Add health check endpoint"
```

## What “complete” means

| Claim | Meaning |
|---|---|
| Software complete | Code paths exist and tests pass |
| Intelligence complete | Eval scores rise with larger trained checkpoints |
| Never | Fabricating 70B `.pt` files without training |
