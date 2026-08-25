# OM AI GENESIS PLATFORM — CURSOR EXECUTION MASTER PROMPT v1.0

**Use:** Paste this entire document as a single Cursor Agent prompt.  
**Repo:** `om-ai-operating-brain` (local path may include a trailing space / version suffix).  
**Mode:** Inspect → map → extend → verify. **Never destroy working OM code.**

---

## MASTER OBJECTIVE

Build / complete a self-hosted **OM AI Cognitive Operating System** so OM can:

reason · remember · learn · use tools · manage agents · understand knowledge · generate code · evaluate itself · improve continuously · scale toward OM-1B / OM-7B / OM-70B

**Target architecture (logical layers):**

```text
USER → OM INTERFACE → OM COGNITIVE OS
  1 Intelligence Core
  2 Reasoning Engine
  3 Knowledge Brain
  4 Memory System
  5 Agent System
  6 Tool System
  7 Coding Intelligence
  8 Multimodal System
  9 Evaluation System
 10 Continuous Learning
 11 Training Pipeline
 12 Security Layer
 13 Enterprise Layer
        ↓
OM FOUNDATION MODEL (OM-1.0 → OM-7 → OM-70B)
        ↓
DIGITAL + PHYSICAL WORLD
```

**Non-goals:** Do not fabricate large model weight files. Do not claim ChatGPT-equal intelligence without trained weights. Do not replace OM-native serve with third-party LLM as default.

---

## HARD RULES (MUST OBEY)

1. **Inspect first.** Before creating any file, inventory existing packages under `om_ai/` and docs. Prefer extend over rewrite.
2. **No destructive rewrites.** Do not delete or gut: `om_ai/api/`, `om_ai/runtime/`, `om_ai/model/`, `om_ai/training/`, `om_ai/agents/`, `om_ai/memory/`, `om_ai/security/`, chat UI, existing CLIs, checkpoints, `.env`.
3. **Reuse map (authoritative).** If a target folder already maps to an existing package, **upgrade that package** instead of inventing a duplicate tree.

| Target (spec) | Existing (prefer) |
|---|---|
| `core/intent_engine` | `om_ai/understanding/`, `om_ai/cognition/`, `om_ai/core/reasoning/analyzer.py` |
| `core/reasoning` | `om_ai/core/reasoning/` + `om_ai/reasoning/` |
| `core/response` | `om_ai/response_engine/` |
| `knowledge/*` | `om_ai/knowledge/`, `om_ai/knowledge_brain/`, `om_ai/knowledge_universe/` |
| `memory/*` | `om_ai/memory/` |
| `agents/*` | `om_ai/agents/`, `om_ai/agent/` |
| tools | `om_ai/actions/`, agent tools, `om_ai/integrations/` |
| coding | `om_ai/agent/coding_agent.py` |
| evaluation | `om_ai/eval/`, `om_ai/evaluation/`, `benchmarks/` |
| learning | `om_ai/learning/`, `om_ai/continuous/` |
| training | `om_ai/training/`, `configs/`, `training/` |
| multimodal | `om_ai/multimodal/`, `om_ai/vision/`, `om_ai/voice/` |
| security | `om_ai/security/` |
| enterprise | `om_ai/tenancy/`, auth/RBAC, observability |
| system build | `om_ai/system/`, `om_ai/foundation/` |

4. **Thin adapters OK.** If the spec demands a path like `om_ai/core/intent_engine/`, create a thin package that re-exports / wraps existing logic — do not duplicate engines.
5. **Verify after each phase.** Run tests / CLI smoke; keep `om-ai system check` green.
6. **Honesty.** Report what is software-complete vs what still needs GPU + data.
7. **Commit only if the user asks.**

---

## PHASE 0 — REPOSITORY INSPECTION (MANDATORY FIRST)

Run and summarize:

```bash
pwd
ls om_ai
om-ai --help | head -80
om-ai system check
om-ai knowledge status
ls configs training docs artifacts/checkpoints 2>/dev/null | head -50
```

Produce a short **EXISTING vs MISSING** matrix for the 13 layers. Only implement MISSING / WEAK items.

Also read:

- `docs/OM_PRODUCTION_FOUNDATION.md`
- `docs/OM_CHATGPT_GAP_ANALYSIS.md`
- `docs/OM_COMPLETION_ROADMAP.md`
- `docs/OM_AI_GENESIS_PLATFORM_V1.md` (if present)

---

## PHASE 1 — CORE INTELLIGENCE

**Goal:** Intent → route → agent → response quality.

Implement / upgrade under `om_ai/core/`:

```text
core/
├── intent_engine/   # classifier, router, task_detector (wrap understanding/)
├── reasoning/       # already present — ensure pipeline wired
└── response/        # formatter + quality (wrap response_engine/)
```

**Flow to support:**

`Create React login page` → Intent=Coding · Domain=Frontend · Framework=React → Coding Agent → generate → security/quality review → final code.

**CLI:** `om-ai reason "..."` must still work; add `om-ai intent classify "..."` if missing.

**API (optional):** `POST /api/reasoning/analyze` already exists — keep compatible.

---

## PHASE 2 — KNOWLEDGE BRAIN

**Goal:** Store/retrieve books, papers, docs, code, company knowledge.

Upgrade (do not replace):

- `om_ai/knowledge/` — ingestion, retrieval, graph
- `om_ai/knowledge_brain/` — eras/domains 1600–2026
- `om_ai/knowledge_universe/` — bucket layout
- data trees under `data/om-knowledge-*`

Ensure corpus buckets exist (create if missing, don’t wipe):

science · engineering · programming · ai · history · business · mathematics · robotics · electronics (+ papers/books/docs as already defined)

**CLI must work:**

```bash
om-ai knowledge status
om-ai knowledge init
om-ai knowledge ingest <file>
om-ai knowledge-universe init
om-ai knowledge-brain catalog
```

---

## PHASE 3 — REASONING ENGINE

Upgrade from Q→A to:

Understand → Analyze → Decompose → Plan → Knowledge → Solve → Verify → Improve → Answer

Ensure `om_ai/core/reasoning/{analyzer,planner,solver,verifier,reflection,pipeline}.py` are the single path used by CLI + API.

Add regression test: `om-ai reason "Design a school management system"` returns structured sections (not “I don’t know”).

---

## PHASE 4 — MEMORY SYSTEM

Upgrade `om_ai/memory/` with layered APIs (SQLite OK):

| Layer | Purpose |
|---|---|
| Short | current turn buffer |
| Conversation | thread history |
| User | preferences / facts |
| Project | stack, repo decisions (e.g. ECTS / FastAPI) |
| Experience | past outcomes |
| Skill | reusable procedures |

Do **not** break existing `sqlite_memory` schemas — migrate additively.

CLI smoke: store/recall project memory for a sample project key.

---

## PHASE 5 — AGENT SYSTEM

Extend `om_ai/agents/` master orchestration:

OM Master → Coding · Research · Database · Security · DevOps · Business · Science · Hardware · Robotics

Reuse existing role engines. Add missing role stubs with clear capabilities; wire tool selection.

Coding Agent abilities (dry-run first): read repo · understand files · plan · modify (gated) · tests · debug.

CLI: `om-ai coding plan --root . --task "..."` must remain valid.

---

## PHASE 6 — CODING INTELLIGENCE

Create thin `om_ai/coding_brain/` **or** extend `om_ai/agent/coding_agent.py` with:

- language/framework skill index (Python, JS/TS, Java, C++, Rust, Go, PHP, SQL, React, Next, FastAPI, Laravel, Spring…)
- capabilities: generate · explain · fix · architecture · security review · testing
- prefer dry-run + plan files; never silent mass file writes

---

## PHASE 7 — TOOL SYSTEM

Unify under `om_ai/tools/` as a **registry facade** over `om_ai/actions/` + existing tools:

File · Terminal (allowlist) · Browser (gated) · Database · API client · Git · Cloud/Automation stubs

Flow: Brain → Tool Selection → Execution → Result Analysis

Respect `OM_AI_ALLOWED_SHELL` and security SSRF rules.

---

## PHASE 8 — EVALUATION SYSTEM

Expand `om_ai/evaluation/` + `om_ai/eval/` + `benchmarks/`:

Reasoning · Coding · Math · Knowledge · Agent · Safety · (optional long-context)

```bash
om-ai evaluate run
# expect score report + artifacts/eval/*.json
```

Keep heuristic mode for no-GPU; optional `--model` path when checkpoint available.

---

## PHASE 9 — CONTINUOUS LEARNING

Close loop in `om_ai/learning/` + `om_ai/continuous/`:

Conversation → Feedback → Quality check → Training example → Dataset → Fine-tune recipe → Better OM

Must work:

```bash
om-ai feedback add ...
om-ai continuous export --out data/continuous/
# POST /api/learning/feedback
```

---

## PHASE 10 — TRAINING + MULTIMODAL + ENTERPRISE (SOFTWARE READY)

**Training:** Ensure configs/scripts for OM-1.0 → 1B → 7B → 70B remain; document GPU handoff; never invent weights.

**Multimodal:** Wire stubs in `vision/` / `voice/` / `multimodal/` with clear `unavailable` errors until weights exist.

**Security:** Keep auth, RBAC, audit, sandbox, permissions.

**Enterprise:** Extend tenancy / API keys / monitoring / usage hooks without breaking single-user local default.

**Self-improvement loop:** Experience → Eval → Weakness → Training data → Improve → New OM version (software orchestration only).

---

## REQUIRED DELIVERABLES

1. Code changes that fill gaps (adapters + real upgrades).
2. `docs/OM_AI_GENESIS_PLATFORM_V1.md` updated with **EXISTING vs IMPLEMENTED** status board.
3. Tests under `tests/` for new public APIs (intent, memory layers, tools registry, coding_brain).
4. `om-ai system build` / `om-ai system check` still **all_passed**.
5. Final report JSON: `artifacts/GENESIS_PLATFORM_REPORT.json` with:

```json
{
  "name": "om-genesis-platform-v1",
  "verified": true,
  "layers": { "intelligence_core": "ok", "...": "ok|partial|external" },
  "external_only": ["OM-1B/7B/70B weights", "massive licensed corpora", "GPU train time"]
}
```

---

## VERIFICATION CHECKLIST (END)

```bash
om-ai system build
om-ai system check
om-ai knowledge status
om-ai reason "Create React login page"
om-ai evaluate run
om-ai continuous export --out data/continuous/
om-ai coding plan --root . --task "Add health check"
curl -s http://127.0.0.1:8080/health   # if serve running
python -m pytest tests/test_system_build.py tests/test_foundation_upgrade.py -q
```

Chat UI at `/chat` must still load (do not break static chat).

---

## IMPLEMENTATION ORDER (STRICT)

1. Phase 0 inspect  
2. Core Intelligence  
3. Knowledge Brain  
4. Reasoning Engine  
5. Memory System  
6. Agent System  
7. Coding Intelligence  
8. Evaluation  
9. Continuous Learning  
10. Training / Multimodal / Enterprise readiness  

---

## SUCCESS DEFINITION

After execution, OM AI must honestly claim:

- ✅ Own platform  
- ✅ Own memory (layered APIs)  
- ✅ Own agents  
- ✅ Own knowledge engine  
- ✅ Own reasoning system  
- ✅ Own evaluation  
- ✅ Own learning pipeline  
- ✅ Own training pipeline (software)  
- ✅ Ready for OM-1B/7B/70B **training path** (not fake weights)  
- ✅ Ready for multimodal expansion (stubs wired)  
- ✅ Ready for hardware/robotics stubs  

**Still external:** large trained weights · licensed data volume · GPU compute.

---

## START COMMAND FOR THE AGENT

Begin now with Phase 0 inspection. Output the EXISTING vs MISSING matrix, then implement Phase 1 onward without destroying current work. Prefer thin adapters over duplicate packages. Keep all existing CLI entry points working.
