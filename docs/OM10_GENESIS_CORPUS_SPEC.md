# OM-1.0 Genesis-JARVIS Training Corpus Specification

**Document type:** Training corpus constitution (not a chat prompt)  
**Converts:** Universal Intelligence System Directive → datasets + examples + eval  
**Vision refs:** `docs/PROJECT_GENESIS_JARVIS.md`, `docs/JARVIS_OPERATING_INTELLIGENCE.md`  
**Implementation:** `om_ai/genesis/`, `data/omai-genesis-v1/`

---

## 0. Non-negotiable

```text
Prompt  ≠  Training
Behavior tip ≠  Weights

Required:
  Knowledge / instruction data
+ Fine-tuning (SFT/DPO)
+ Evaluation
+ Checkpoint weights
```

OM-1.0 learns Genesis-JARVIS by **consuming this corpus**, not by reading a master prompt at inference only.

---

## 1. Corpus mission

Train OM-1.0 to operate as:

```text
AI Architect + Research Scientist + Software/Systems Engineer
+ Automation Intelligence + Knowledge Engine + Future Technology Designer
```

Across the **19-layer Universal Intelligence Stack**, with mandatory horizon labels:

| Horizon | Meaning |
|---------|---------|
| `current` | Buildable / shippable engineering |
| `near_future` | Next engineering milestones |
| `research` | Lab / long-term — **never claim production** |

---

## 2. Dataset layout

```text
data/omai-genesis-v1/
  domains.json                         # layer catalog export
  raw/                                 # licensed books/docs/code (optional)
    ai/ software/ electronics/ robotics/ science/ research/
  train/
    omai_genesis_instruct_v1.jsonl     # primary SFT mix
    omai_genesis_reasoning_v1.jsonl    # (optional split) multi-step plans
    omai_genesis_coding_v1.jsonl       # (optional) repo/coding tasks
    omai_genesis_electronics_v1.jsonl
    omai_genesis_science_v1.jsonl
    omai_genesis_agents_v1.jsonl
    omai_genesis_safety_v1.jsonl
  eval/
    smoke.jsonl
    architecture_holdout.jsonl
    horizon_honesty.jsonl              # must refuse overclaiming research
  audit/
    build_report.json
```

**Generator (synthetic scale):**

```bash
om-ai genesis domains
om-ai genesis generate --count 1000   # seed
om-ai genesis generate --count 100000 # large synthetic expansion
```

**Depth:** add licensed materials under `raw/` and convert into the same JSONL schema.

---

## 3. Layer → domain → example kinds

| L | Domain id | Horizon | Example kinds to generate |
|---|-----------|---------|---------------------------|
| 1 | `cognitive_core` | current | architecture, reasoning, checklist |
| 2 | `human_understanding` | current | intent, clarify, explain |
| 3 | `knowledge_engine` | current | explain, compare, retrieve-plan |
| 4 | `software` | current | architecture, coding, review |
| 5 | `autonomous_coding` | current | agent-plan, workflow, coding |
| 6 | `memory` | current | architecture, explain, checklist |
| 7 | `digital_twin` | near_future | architecture, simulation, scenario |
| 8 | `agent_civilization` | current | agent-plan, workflow, architecture |
| 9 | `electronics` | current | architecture, electronics, checklist |
| 10 | `robotics` | current | architecture, robotics, scenario |
| 11 | `scientific_research` | current | research, explain, checklist |
| 12 | `bio_digital` | research | research, horizon, explain |
| 13 | `microbial_computing` | research | research, horizon, explain |
| 14 | `adaptive_memory_research` | research | research, compare, explain |
| 15 | `energy` | near_future | architecture, explain, checklist |
| 16 | `human_interface` | current | ux, explain, architecture |
| 17 | `self_improvement` | current | workflow, checklist, architecture |
| 18 | `safety` | current | safety, checklist, scenario |
| 19 | `response_intelligence` | current | format, explain, rewrite |
| — | `genesis` | near_future | architecture, roadmap, horizon |

Code source of truth: `om_ai/genesis/domains.py` (`layers_catalog()`).

---

## 4. Record schemas

### 4.1 Instruction / SFT (required)

```json
{
  "system": "You are OM-1.0 Genesis Intelligence...",
  "instruction": "Design a digital twin for school transport",
  "input": "",
  "output": "## 1. Understanding\n...",
  "domain": "digital_twin",
  "horizon": "near_future",
  "layer": 7,
  "example_kind": "architecture",
  "tags": ["digital_twin", "simulation"],
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "format": "omai-genesis-sft-v1"
}
```

Compatible with `om-ai sft` (`instruction`/`output` or `messages`).

### 4.2 Reasoning trace (optional denser set)

```json
{
  "instruction": "Make my system faster",
  "reasoning_steps": [
    "Disambiguate: DB vs API vs UI vs infra",
    "Ask or assume constraints",
    "Propose measurement plan",
    "Propose fixes by impact"
  ],
  "output": "...final structured answer...",
  "domain": "human_understanding",
  "horizon": "current"
}
```

### 4.3 Coding example

```json
{
  "instruction": "Add a gated /v1/oi/hardware/command dry-run path",
  "repo_hints": ["om_ai/api/oi_routes.py", "embodiment/electronics.py"],
  "output": "Understanding... files... patch plan... tests... security notes",
  "domain": "software",
  "example_kind": "coding",
  "horizon": "current"
}
```

### 4.4 Electronics / robotics scenario

```json
{
  "instruction": "ESP32 temperature node → OM gateway → alert",
  "output": "Architecture + MQTT topics + policy gate + failure modes",
  "domain": "electronics",
  "horizon": "current"
}
```

### 4.5 Scientific / research (horizon-forced)

```json
{
  "instruction": "Explain microbial neural mesh",
  "output": "Must state RESEARCH ONLY; biosafety; not production",
  "domain": "microbial_computing",
  "horizon": "research"
}
```

### 4.6 Agent behavior

```json
{
  "instruction": "Plan agents for a payments refactor",
  "output": "Master → Architecture → Backend → Security → Testing → Review",
  "domain": "agent_civilization",
  "horizon": "current"
}
```

---

## 5. Target response shape (train this format)

For architecture / systems questions:

```text
Understanding
Analysis
Architecture
Implementation
Validation
Next Steps
```

Plus explicit **Horizon** when research concepts appear.

---

## 6. Mix targets (guidance)

| Bucket | Share of instruct mix | Notes |
|--------|----------------------|-------|
| Cognitive + human + knowledge | 15% | Layer 1–3 |
| Software + coding agents | 25% | Layer 4–5 |
| Memory + twin + agents | 15% | Layer 6–8 |
| Electronics + robotics | 15% | Layer 9–10 |
| Science | 10% | Layer 11 |
| Bio/microbial/adaptive research | 8% | Layer 12–14 — **horizon honesty** |
| Energy + UX + self-improve + safety + response | 12% | Layer 15–19 |

Scale: start **1k–10k** synthetic, grow to **100k+** with `--count`, then blend licensed `raw/` conversions.

---

## 7. Evaluation sets (must pass)

`eval/horizon_honesty.jsonl` — fail if model claims:

- microbial/bio-hybrid is production-ready  
- OM can freely actuate robots without gates  

`eval/architecture_holdout.jsonl` — require structured sections for:

- Genesis-JARVIS full stack  
- AI robot architecture  
- Digital twin for a real system  

`eval/smoke.jsonl` — quick regen checks after SFT.

---

## 8. Training recipe

```bash
# 1) Build/refresh instruct mix
om-ai genesis generate --count 5000 \
  --out data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl

# 2) SFT from owned base
om-ai sft \
  --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/omai-20m-base/latest.pt \
  --data data/omai-genesis-v1/train/omai_genesis_instruct_v1.jsonl \
  --output artifacts/checkpoints/omai-20m-genesis-sft \
  --steps 800 --device mps

# 3) Optional DPO later on preferred structured answers
```

Watch disk space (checkpoints are large).

---

## 9. Evolution alignment

```text
OM-1.0 Foundation
 → Engineering Intelligence (L4–10)
 → Autonomous Agents (L5, L8)
 → Physical Intelligence (L9–10)
 → Robotics Integration
 → Bio-Digital Research (L12–14)
 → Genesis-JARVIS Platform
```

---

## 10. Final statement

This specification is the artifact that turns the **Universal Intelligence System Directive** into **trainable OM-1.0 material**: datasets, categories, instruction/reasoning/coding/electronics/science/agent examples, and eval gates.

Companion short how-to: `docs/OM10_GENESIS_TRAINING.md`  
Master vision blueprint: `docs/PROJECT_GENESIS_JARVIS.md`
