# OM AI Operating Brain — Full Project Blueprint

Canonical map of **repository structure**, **production runtime paths**, and **what is real vs scaffold**.  
Use this as the single blueprint for completing and operating the project.

Related docs: [ARCHITECTURE.md](ARCHITECTURE.md) · [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) · [COMPANION_PAGE.md](COMPANION_PAGE.md) · [OM_JARVIS_MASTER_PLAN.md](OM_JARVIS_MASTER_PLAN.md)

---

## 1. Product surfaces (what users hit)

| URL / command | Purpose | Primary code |
|---------------|---------|--------------|
| `http://127.0.0.1:8080/companion` | Jarvis human companion (voice + HUD) | `om_ai/api/companion/`, `om_ai/core/companion_runtime/` |
| `http://127.0.0.1:8080/chat` | Workspace chat UI | `om_ai/api/static/chat.html`, `/v1/chat` |
| `om-ai serve` | FastAPI production server | `om_ai/api/main.py` |
| `om-ai chat` / `om-ai generate` | CLI inference | `om_ai/cli.py`, `om_ai/backends/om_native.py` |
| `om-ai train-om1` | Local OM-1.0 training | `om_ai/training/` |

---

## 2. Top-level repository layout

```text
om-ai-operating-brain/
├── om_ai/                    # Python package (all product code)
├── configs/                  # Model shapes (tiny → 70B) — shapes, not weights
├── docs/                     # Architecture, roadmaps, companion, training
├── artifacts/                # Checkpoints, sqlite, tokenizer, runtime data
├── data/                     # Corpora / training inputs (local)
├── scripts/                  # Train / pack / ops helpers
├── tests/                    # pytest suite
├── om_companion_app/         # Optional companion front-end app
├── om_desktop/               # Optional desktop shell
├── .env / .env.example       # Runtime config (checkpoint, device, features)
├── pyproject.toml            # Package + CLI entry `om-ai`
└── README.md                 # Quick start + honesty notes
```

---

## 3. `om_ai/` package map (91 top-level areas)

### 3.1 Production spine (use these first)

| Layer | Path | Role |
|-------|------|------|
| API | `om_ai/api/` | FastAPI routes, auth, static UI, companion WS |
| Native model | `om_ai/backends/om_native.py`, `om_ai/model/` | Load checkpoint + generate |
| Chat cascade | `om_ai/runtime/chat_backend.py` | Production reply cascade (no external LLM by default) |
| ChatGPT-like controller | `om_ai/core/chatgpt_runtime/` | STEP 30 front door |
| Chat intelligence | `om_ai/core/chat_intelligence/` | Intent → plan → solve → quality |
| Production brain | `om_ai/core/brain_runtime/production_brain.py` | Routed production controller |
| Companion OS | `om_ai/core/companion_os/`, `companion_runtime/` | Voice session + turn loop |
| Companion brain | `om_ai/core/companion_brain/` | Semantic companion turn |
| Human companion | `om_ai/core/human_companion/` | Emotion, friend mind, personality, presence |
| Memory | `om_ai/memory/`, `core/human_memory/`, `core/companion_memory/` | Persistent + session memory |
| Knowledge / RAG | `om_ai/knowledge/`, `live_knowledge/` | Local retrieval + live HTTP stubs |
| Agents / tools | `om_ai/agents/`, `actions/`, `tools/` | Plan → tool → verify |
| Security | `om_ai/security/` | Keys, RBAC, SSRF, audit, rate limits |
| Training | `om_ai/training/`, `corpus/`, `tokenizer/` | Pretrain / SFT / DPO pipeline |

### 3.2 Companion / Jarvis stack (core)

```text
om_ai/core/
├── companion_runtime/     # Session, STT/TTS glue, handle_text
├── companion_brain/       # Semantic turn + response engine
├── companion_os/          # OS façade over brain + actions + presence
├── companion_personality/ # Voice presence, speech shaping, garbage filters
├── companion_memory/      # Companion memory service
├── companion_security/    # Permission gates for actions
├── human_companion/       # Emotion, friend_mind, platform turn spine
├── human_dialogue/        # Dialogue modes
├── human_memory/          # Episodic / profile memory
├── jarvis_brain/          # Jarvis pipeline entry
├── voice_engine/          # Delivery / TTS helpers
├── presence_engine/       # Avatar / presence signals
└── wellbeing/             # Soft support routing
```

### 3.3 Chat / reasoning / knowledge (core)

```text
om_ai/core/
├── chat_intelligence/     # Orchestrator, router, solution, stub_detect
├── chatgpt_runtime/       # OMBrainController
├── brain_runtime/         # OMProductionBrain
├── brain_router/          # Multi-model / research routing
├── reasoning/             # Analyze → plan → solve → verify
├── intelligence/          # real_answer, capability router
├── response/              # Response intelligence / formatting
├── research/ + deep_research/ + research_intelligence/
├── knowledge_* / knowledge_brain/
└── continuous_learning/
```

### 3.4 Other `om_ai/` domains (present in tree)

Training & data: `training/`, `training_pipeline/`, `corpus/`, `data/`, `data_engine/`, `data_pipeline/`, `tokenizer/`, `checkpoint/`, `registry/`  
Cognition: `understanding/`, `reasoning/`, `cognition/`, `cognitive/`, `decision/`, `reflection/`  
Embodiment: `vision/`, `voice/`, `multimodal/`, `perception/`, `avatar/`, `om_avatar/`, `robotics/`  
Platform: `platform/`, `enterprise/`, `tenancy/`, `observability/`, `security/`, `safety/`  
Autonomy: `autonomous/`, `autonomy/`, `operating_intelligence/`, `orchestration/`, `workflow/`  

> Many packages are **scaffolds or partial**. Prefer the production spine above for shipping paths.

---

## 3.5 Final Companion Architecture (13 layers)

Canonical runtime: `om_ai.core.companion_architecture.CompanionPipeline`

```text
USER (Voice / Text)
  → 1  Human Understanding     om_ai/core/human_intelligence/
  → 2  Emotion & Empathy       om_ai/core/emotion_intelligence/
  → 3  Memory                  om_ai/core/memory/ + companion_memory + knowledge_growth
  → 4  Conversation Intel      om_ai/core/dialogue_intelligence/
  → 5  Reasoning               om_ai/core/reasoning/ + chat_intelligence
  → 6  Knowledge (RAG)         om_ai/core/knowledge/ → om_ai/knowledge/  (NOT 100M prompts)
  → 7  Research                om_ai/core/deep_research/ + companion_runtime/search_care
  → 8  Action + Permission    om_ai/core/action_control/
  → 9  Personality (brother)   om_ai/core/personality/ + companion_personality
  → 10 Voice                   om_ai/core/voice/ → voice_intelligence
  → 11 Avatar / Presence       om_ai/core/avatar/ → presence_engine
  → 12 Self Improvement        om_ai/core/self_learning/ → self_improvement
  → 13 Companion Runtime       om_ai/core/companion_runtime/
```

**Behavior contracts**

| Behavior | Rule |
|----------|------|
| Search / Google | Research + summarize. **Do not open browser** unless user says `go` / `open` / `kholo` |
| Knowledge growth | Vector retrieval + `artifacts/companion/knowledge_growth/` notes — not stuffing millions of prompts |
| Bond | Brother / bhai — warm, human, not helpdesk |
| Emotions | Angry / happy / sad / tired / romantic(care) mirrored in tone |
| Actions | Ask permission before opening projects/apps when risk is sensitive |

**Example turns**

- `"I had a bad day"` → listen / supportive (not “explain your problem”)
- `"search latest AI"` → research summary, browser stays closed
- `"open my project"` → “I found your project. Do you want me to open it?”

## 3.6 STEP 71 — Human Presence Intelligence

Canonical gate (before SolutionEngine / ResponseEngine):

`om_ai.core.human_presence.HumanPresenceEngine`

```text
User → Meaning + Emotion + Intent + Context
     → Personality (care / empathy / relationship)
     → Route: listen | answer | search | action
     → Permission (if side-effect)
     → Natural reply → Voice + Avatar
```

| Contract | Rule |
|----------|------|
| Word ≠ Meaning | `"today was difficult"` → listen, not “explain your problem” |
| Empathy honesty | Understand feelings; **never pretend** to be human / have feelings |
| Search ≠ Open | Summarize first; open only on go/open/kholo + permission |
| Knowledge | Vector retrieval — not 100M prompts in context |
| Improvement | Feedback + failure records in `artifacts/companion/self_learning/` |

Files: `human_intelligence/human_meaning_engine.py`, `response_behavior.py`, `emotion_intelligence/emotion_state.py`, `action_control/action_policy.py`, `execution_guard.py`, `personality/conversation_principles.py`.

---

## 4. Production runtime blueprints

### 4.1 Companion (`/companion`)

```text
Browser HUD (static/companion)
        │  POST /api/companion/message  (+ WS)
        ▼
CompanionRuntime.handle_text
        │
        ├─ Voice ingest / HCI hold / presence.thinking
        ├─ Action plan + permission gate (SENSITIVE asks first)
        ├─ CompanionPipeline (13-layer architecture)  ← fast human path
        │     understand → emotion → memory → dialogue
        │     → research (no browser) / reason / knowledge
        │     → personality (brother) → human reply
        ├─ Companion brain / production brain (complex asks)
        └─ shape_for_speech → TTS + avatar state
```

**Hard rules (implemented):**
- Never speak solution stubs (`Solve: … 1. understand …`)
- Prefer native model when `OM_MODEL_CHECKPOINT` loads
- Fallback = grounded `real_answer` / helpful defaults — **not** static outlines
- Search does **not** open Google unless user says go/open/kholo
- OM speaks as brother/bhai — not a robot helpdesk

### 4.2 Workspace chat (`/chat` → `/v1/chat`)

```text
chat.html
   → POST /v1/chat
   → runtime/chat_backend.chat_reply
        ├─ chatgpt_runtime (STEP 30)
        ├─ chat_pipeline
        ├─ operating_intelligence
        └─ native OM generate
```

### 4.3 CLI production brain

```text
OMProductionBrain.process(message)
   → ConversationRouter
   → emotional / research / action specialists when needed
   → else OMBrainController + model_generate (native/local)
   → safety + quality
```

---

## 5. Chat intelligence blueprint

```text
User message
  → IntentUnderstanding
  → ConversationEngine (name / social only)
  → AnswerPlanner
  → SolutionEngine  (ONLY debugging/coding/howto/…)
  → model_generate  (preferred whenever available)
  → ResponseOptimizer + Correction + Safety + Quality
  → answer
```

Stub detection: `om_ai/core/chat_intelligence/stub_detect.py`  
Reject patterns like “incorrect assumptions / direct path for: Solve:”.

---

## 6. Model / checkpoint reality

| Item | Truth |
|------|--------|
| `configs/*.json` | Architecture **shapes** only |
| `artifacts/checkpoints/om-1.0-*/latest.pt` | Real local weights (quality varies) |
| Recommended serve checkpoint | Prefer chat DPO/SFT or `om-1.0-long` if valid |
| Device | `OM_MODEL_DEVICE=mps` only if MPS available; else `cpu` / `cuda` |
| Missing / unloadable checkpoint | Native generate unavailable → grounded fallbacks (no third-party LLM by default) |

Example `.env` (production-oriented):

```bash
OM_MODEL_PROVIDER=om_native
OM_MODEL_CHECKPOINT=artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt
OM_AI_CHECKPOINT=artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt
OM_MODEL_TOKENIZER=artifacts/tokenizer-production-65536.json
OM_MODEL_CONFIG=configs/om-1.0-local.json
OM_MODEL_DEVICE=mps   # or cpu / cuda
OM_AI_AUTOLOAD=1
```

---

## 7. Data & artifacts

```text
artifacts/
├── checkpoints/          # om-1.0-long, chat-sft, chat-dpo, smoke, …
├── models/om-1.0/        # Registry metadata
├── tokenizer-*.json
├── om_ai.sqlite3         # App / prompts
├── om_ai_rag.sqlite3     # RAG store
└── companion/            # Companion memory / presence data
```

---

## 8. Implementation status (honest)

| Area | Status |
|------|--------|
| FastAPI serve + auth + workspace UI | **Working** |
| Companion page + voice session API | **Working** (quality depends on weights) |
| Chat intelligence + stub rejection | **Working** (post-fix) |
| Native OM-1.0 load/generate | **Working when checkpoint+device OK** |
| Solution template stubs as answers | **Blocked** |
| Frontier ChatGPT-level intelligence | **Not claimed** — needs real training data + GPU |
| Many `om_ai/core/*` packages | Scaffold / partial — not all on hot path |

---

## 9. How to run the full production loop

```bash
cd "/path/to/om-ai-operating-brain 3"
source .venv/bin/activate

# Ensure .env points at a real checkpoint + valid device
om-ai model-info
om-ai serve --host 127.0.0.1 --port 8080

# Companion
open http://127.0.0.1:8080/companion

# Workspace chat
open http://127.0.0.1:8080/chat
```

Smoke CLI brain:

```bash
python - <<'PY'
from om_ai.core.brain_runtime import OMProductionBrain
om = OMProductionBrain()
print(om.process("hii")["answer"])
PY
```

---

## 10. Completion checklist (production companion chat)

- [x] Block `Solve:` / “incorrect assumptions” stubs
- [x] Prefer model / real_answer over templates
- [x] Companion garbage / stub filters
- [x] Production brain routes to controller + model_generate
- [x] 13-layer CompanionPipeline architecture wired
- [x] Search without browser redirect (unless go/open/kholo)
- [x] STEP 71 Human Presence (why before what) before SolutionEngine
- [x] Empathy without pretending to be human
- [x] Search ≠ open + permission guard
- [x] Conversation principles in personality
- [ ] Valid checkpoint loaded on serve host (check banner: `Status: READY`)
- [ ] Device matches hardware (`mps` / `cuda` / `cpu`)
- [ ] Restart `om-ai serve` after code changes
- [ ] Hard-refresh companion UI

---

## 11. Where to change what

| Goal | Edit |
|------|------|
| Companion reply quality | `companion_architecture/`, `companion_brain/`, `human_companion/`, `chat_intelligence/` |
| Search without open | `companion_runtime/search_care.py` |
| Brother personality | `personality/identity.py`, `companion_personality/personality_rules.py` |
| Stop bad templates | `chat_intelligence/stub_detect.py`, `explanation_engine.py`, `voice_presence.py` |
| Native model load | `.env`, `backends/om_native.py` |
| API routes | `api/main.py`, `api/companion/routes.py` |
| Chat UI look | `api/static/chat.html` |
| Training | `training/`, `configs/`, `docs/TRAINING.md` |

---

*This blueprint reflects the tree and hot paths as of the production companion/chat fix wave. Prefer code on the production spine over unused parallel packages.*
