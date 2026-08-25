# OM Universal Knowledge Brain (1600–2026)

Build a **knowledge ecosystem**, not a single mega-text dump into weights.

```
OM AI
  └─ Knowledge Intelligence Layer
       ├─ Historical eras (1600–2026)
       ├─ Domain brains (math, physics, CS, AI, …)
       ├─ Vector / RAG retrieval
       ├─ Instruction SFT rows
       └─ Reasoning + agents + memory
```

## Eras

| Era | Years | Focus |
|---|---|---|
| 1 | 1600–1700 | Scientific Revolution |
| 2 | 1700–1800 | Enlightenment + industrial foundation |
| 3 | 1800–1900 | Industrial Revolution |
| 4 | 1900–1950 | Relativity, quantum, computing foundations |
| 5 | 1950–2000 | Computer revolution + AI history |
| 6 | 2000–2020 | Internet, cloud, deep learning |
| 7 | 2020–2026 | Transformers, LLMs, agents, RAG |

## Domains (folders under `data/om-knowledge-brain-v1/knowledge/`)

`history`, `mathematics`, `physics`, `chemistry`, `biology`, `medicine`, `engineering`, `electronics`, `robotics`, `programming`, `computer_science`, `artificial_intelligence`, `business`, `psychology`, `philosophy`, `future_technology`

Each domain: `raw/` → `cleaned/` → `chunks/` → `embeddings/`

## Levels

1. **Knowledge base** — licensed docs/books/papers in `raw/`  
2. **RAG** — retrieve → OM reason → answer  
3. **Fine-tune** — style, reasoning, domain skills (SFT/DPO)  
4. **Pretrain scale** — OM-1.0 → OM-7.0 → OM-70.0 with real compute  

## CLI

```bash
om-ai knowledge-brain catalog
om-ai knowledge-brain init --root data/om-knowledge-brain-v1
om-ai knowledge-brain generate --count 5000 \
  --out data/om-knowledge-brain-v1/train/om_knowledge_instruct_v1.jsonl
```

Master directive (prompt extract): [`prompts/OM_AI_UNIVERSAL_KNOWLEDGE_DIRECTIVE.md`](prompts/OM_AI_UNIVERSAL_KNOWLEDGE_DIRECTIVE.md)

## What “complete” means here

- **Complete architecture + domain map + eras + pipelines:** yes (this doc + package)  
- **Complete literal dump of all human knowledge 1600–2026 inside one checkpoint:** no — continuous corpus growth + RAG + training  

Add licensed sources into `knowledge/<domain>/raw/` and grow volume over time.
