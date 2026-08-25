# OM AI — JARVIS-Level Operating Intelligence

**Parent blueprint:** [`PROJECT_GENESIS_JARVIS.md`](PROJECT_GENESIS_JARVIS.md) (Chief Architect constitution)

**Clarification:** A real JARVIS is not a prompt. A prompt shapes behavior. The system is:

```text
Model + Memory + Sensors + Tools + Robotics + Electronics
+ Knowledge + Learning + Hardware Integration + Experience UI
(+ future Bio-Digital Research — not a complete shippable machine today)
```

This document converts the vision into an **engineering roadmap** Cursor can build module-by-module.

## Core cycle (every task)

```text
Observe → Understand → Think → Plan → Execute → Verify → Improve
```

Implemented entrypoint: `om_ai.operating_intelligence.facade.run_cycle(...)`

## Capability map (repo truth)

| # | Vision area | Status | Implementation |
|---|-------------|--------|----------------|
| 1 | Human understanding | PARTIAL | `om_ai/understanding/`, `agent/intent.py` |
| 2 | Long-term memory | EXISTS | `om_ai/memory/`, workspace APIs |
| 3 | Reasoning / planning / review | PARTIAL | `reasoning/`, `agent/planner.py`, `verifier.py` |
| 4 | Software engineering agents | PARTIAL | `discovery/`, `agents/`, allow-listed `actions/shell` |
| 5 | Knowledge / RAG / science corpus | EXISTS | `knowledge/`, `live_knowledge/`, `corpus/` |
| 6 | Electronics / IoT / MCU | **MISSING** | stubs: `operating_intelligence/embodiment/electronics.py` |
| 7 | Sensors | **MISSING** | stubs: `embodiment/sensors.py` |
| 8 | Robotics | **MISSING** | stubs: `embodiment/robotics.py` |
| 9 | Voice | PARTIAL | `om_ai/voice/` (scaffold; weights external) |
| 10 | Vision | PARTIAL | `om_ai/vision/`, `multimodal/` |
| 11 | Agent automation / tools | EXISTS | `agents/`, `actions/`, `integrations/` |
| 12 | Digital twin | **MISSING** | stubs: `embodiment/twin.py` |
| 13 | Self-improvement | PARTIAL | `continuous/` + SFT/DPO/PPO |
| 14 | Response experience | EXISTS | `response_engine/` + streaming chat UI |
| 15 | Owned foundation model | PARTIAL | OMAI-20M prove; scale 100M→70B separately |

## Package layout

```text
om_ai/operating_intelligence/
  facade.py                 # Observe→…→Improve cycle
  human/                    # NLU / affect bridges
  cognition/                # plan + review bridges
  memory_bridge.py          # memory + knowledge
  world/                    # code + knowledge world models
  perception/               # voice + vision bridges
  automation/               # tools / agents
  growth/                   # feedback → retrain hooks
  experience/               # response formatting
  embodiment/               # HARDWARE STUBS (safe, not fake-complete)
    electronics.py
    sensors.py
    robotics.py
    twin.py
    gateway.py              # IoT gateway contract
```

Existing packages stay the real implementations. `operating_intelligence/` is the **JARVIS facade** that connects them.

## Build phases (ordered)

### Phase A — Digital brain (NOW → next 1–2 milestones)
1. Strengthen memory (project/code/decision history)
2. Dense RAG embeddings
3. Repo tools: read / patch / git / tests
4. Planner → structured tool calls
5. Critic / verify loop
6. Response experience (done — keep improving)

### Phase B — Perception
1. Wire production STT/TTS adapters behind `voice/`
2. Wire VLM/OCR behind `vision/` when weights exist
3. Multimodal chat turns in UI

### Phase C — Embodiment (physical world)
1. `HardwareControlLayer` API (MQTT/serial/HTTP)
2. Sensor ingest → normalize → decide → act
3. MCU profiles: ESP32 / Arduino / RPi / STM32
4. Robotics controller contract (nav / motors) — sim first
5. Digital twin state sync

### Phase D — Scale intelligence
1. OMAI-100M → 1B → 7B → 70B (see `OWN_INTELLIGENCE_ROADMAP.md`)
2. Domain SFT (code, engineering, robotics manuals — licensed only)
3. Continuous learning from feedback

## APIs to add (contracts)

| Endpoint (planned) | Purpose |
|--------------------|---------|
| `POST /v1/oi/cycle` | Run Observe→Improve on a user goal |
| `GET /v1/oi/status` | Capability matrix (what is live vs stub) |
| `POST /v1/oi/hardware/command` | Send gated hardware command |
| `POST /v1/oi/sensors/ingest` | Ingest sensor reading |
| `GET /v1/oi/twin/{id}` | Digital twin snapshot |

Hardware routes must be **gated** (auth + allow-list + dry-run default). Never auto-execute physical actuators without explicit user/ops approval.

## Honesty rules

- Do **not** claim robotics/IoT “works” until real drivers + hardware tests exist.
- Do **not** replace the owned model with OpenAI/Claude as the brain.
- Prompts guide style; **weights + tools + sensors** create capability.
- Small model + strong OI stack > large model with no memory/tools.

## Master vision prompt (behavior layer)

- Full blueprint: **`docs/PROJECT_GENESIS_JARVIS.md`**
- Short prompt extract: `docs/prompts/OM_AI_JARVIS_OPERATING_INTELLIGENCE.md`  
Chat runtime still uses compact `[OM-RX-v1]` for tiny context windows; Genesis is the long-term architecture constitution.

## Next concrete build slice

Recommended next coding milestone (digital brain, before hardware):

1. Project + decision memory schema  
2. Safe `read_file` / `apply_patch` tools  
3. Dense embedding RAG adapter  
4. `GET /v1/oi/status` capability board in UI  

Then: voice/vision adapters → hardware gateway stubs → MCU dry-run.
