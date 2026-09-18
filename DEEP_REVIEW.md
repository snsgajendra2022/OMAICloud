# OM AI — Deep File & Path Review

> Generated: 2026-09-17  
> Scope: live chat path + cognitive brain stack + API/backends (deep read)

Companion to [`PROJECT.md`](PROJECT.md) (full inventory). This doc is a **deep review** of the production chat/brain path with findings.

---

## Executive verdict

| Area | Verdict | Notes |
|------|---------|-------|
| Live chat path | **Primary** | `chat_backend.chat_reply` → `run_chat_pipeline` (default ON) |
| Cognitive brain | **Secondary / fallback** | `OMCognitiveBrain` via `run_cognitive_brain` / `.process()` after pipeline |
| Knowledge brain (core) | **Integrated in brain** | `om_ai.core.knowledge_brain` used in `brain_pipeline.generate` |
| Knowledge brain (chat) | **Different class** | `chat_pipeline` uses `om_ai.knowledge.brain.AdvancedKnowledgeBrain` |
| Long context + advanced reasoning | **Wired in brain.generate** | Before model; store after answer |
| Conversation intelligence | **Wired** | Early social short-circuit in `generate` |
| Observability / production brain | **Mostly unused in serve** | `OMProductionBrain` not on default chat path |
| Duplicate engines | **Risk** | Multiple ReasoningEngine / KnowledgeBrain / ResponseEngine names |

### Critical findings (fixed or open)

1. **Fixed:** `generate()` conversation early-return used to return a bare **string** (broke callers expecting a dict). Now returns a full result dict.
2. **Fixed:** Conversation router only matched exact `hi`/`hello`/`hey` — expanded to `hello …`, `how are you`, etc.
3. **Open:** Two parallel brains — `chat_pipeline` (serve default) vs `brain_pipeline.generate` (richer) — many new integrations only on `generate`, not on serve path.
4. **Open:** `self.civilization` / `self.autonomous_research` constructed in `__init__` but not called in `generate`/`process`.
5. **Open:** `om_ai/core/observability` duplicated concepts with `om_ai/observability`; ActivityEvent defined twice in core observability.
6. **Open:** ResearchPipeline only creates a `ResearchTask` stub — real research still via `ResearchEngine.research()`.

---

## 1. Live serve call graph

```text
UI /chat  OR  POST /api/v1/chat/completions
    → om_ai/api/openai_compat.py::_run_chat / main.py chat
    → om_ai/runtime/chat_backend.py::chat_reply
         ├─ intelligence.enrich_for_chat (direct_reply?)
         ├─ [OM_CHAT_PIPELINE=1] run_chat_pipeline   ← DEFAULT LIVE PATH
         ├─ [OM_UNIVERSAL_INTELLIGENCE] UniversalIntelligence
         ├─ IntelligenceManager / dynamic agents
         ├─ run_cognitive_brain → OMCognitiveBrain.process()  ← fallback
         ├─ OperatingIntelligence.run
         └─ OM native / openai / external_llms
```

**Important:** New brain features (KnowledgeBrain core, ResearchPipeline, LongContext, AdvancedReasoning, ConversationEngine) live mainly in `OMCognitiveBrain.generate()`. Serve path prefers `run_chat_pipeline`, and cognitive fallback calls **`.process()`**, not `.generate()` — so those integrations may not run in production chat until wired.

---

## 2. Package deep inventory (focus stack)

### Runtime — chat serve path

**13 files · 5647 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/runtime/chat_backend.py` | 1237 | `ResponseEcho` (check)<br>`ChatBackendInfo`<br>`_looks_scripted()`@83<br>`_latest_user_text()`@99<br>`looks_like_web_spam()`@110<br>`_env()`@161<br>`_env_on()`@165<br>`_env_float()`@169 | Chat reply backends: OM native (default), local engine, or OpenAI-compatible API. |
| `om_ai/runtime/chat_orchestrator.py` | 298 | `run_cognitive_brain()`@14<br>`_env_float()`@30<br>`_env_int()`@40<br>`generation_config()`@50<br>`_normalize_messages()`@71<br>`build_chat_messages()`@83 | Chat orchestration: template + generation config + quality gate. |
| `om_ai/runtime/chat_pipeline.py` | 825 | `pipeline_enabled()`@24<br>`run_chat_pipeline()`@33 | OM Chat Pipeline v2 |
| `om_ai/runtime/connectivity_bridge.py` | 799 | `SystemConnectivityBridge` (enrich, status, _import_status, _ping, _looks_coding, _perception, _action_twin, _actions_live)<br>`connectivity_enabled()`@19<br>`_safe()`@28<br>`enrich_chat_turn()`@789<br>`connectivity_status()`@798 | OM System Connectivity Bridge |
| `om_ai/runtime/engine.py` | 522 | `CheckpointTokenizerMismatch`<br>`LocalLLMEngine` (__init__, load, _assert_loaded, generate, generate_stream, _chat_once, chat, generate_with_context)<br>`_repo_root()`@30<br>`_embedding_vocab()`@34<br>`resolve_tokenizer_path_for_checkpoint()`@47<br>`_extra_tokenizer_matches_vocab()`@113<br>`usable_generation_text()`@127<br>`is_degenerate_generation()`@142 | — |
| `om_ai/runtime/evolution_matrix.py` | 433 | `_ensure_repo_root_on_path()`@108<br>`_load_om5()`@116<br>`default_evolution_model()`@137<br>`resolve_model_id()`@146<br>`level_for_model()`@163<br>`level_runtime_profile()`@173 | OM evolution levels L1–L5 for /chat model selection. |
| `om_ai/runtime/external_llms.py` | 397 | `normalize_provider_id()`@104<br>`_env_key()`@148<br>`resolve_api_key()`@156<br>`provider_ready()`@166<br>`_normalize_messages()`@190<br>`_friendly_llm_http_error()`@203 | Optional external LLM connectors (OpenAI-compatible + Anthropic). |
| `om_ai/runtime/intelligence.py` | 407 | `IntelligenceBundle`<br>`_env_flag()`@13<br>`detect_language()`@31<br>`language_instruction()`@47<br>`extract_memory_candidates()`@78<br>`_name_from_memories()`@111<br>`aligned_memory_reply()`@123 | OM AI intelligence layer: instructions, memory, language, RAG, alignment. |
| `om_ai/runtime/live_answer.py` | 271 | `live_enabled()`@9<br>`network_enabled()`@18<br>`needs_live_knowledge()`@63<br>`_wiki_topic()`@82<br>`_is_weak_snippet()`@94<br>`_prefer_hit()`@105 | Live web + Wikipedia grounded answers for chat (no external LLM). |
| `om_ai/runtime/public_reply.py` | 165 | `looks_like_genesis_template()`@55<br>`extract_clean_tool_answer()`@69<br>`_looks_internal()`@95<br>`sanitize_public_reply()`@113<br>`is_safe_public_answer()`@153 | Public reply sanitizer — never leak internals to the user. |
| `om_ai/runtime/session_flags.py` | 64 | `env_flag()`@20<br>`flags_from_settings()`@31<br>`apply_session_flags()`@59 | Per-request feature flags from user Settings (overrides env defaults). |
| `om_ai/runtime/system_prompts.py` | 225 | `SystemPromptStore` (__init__, _ensure_default, get_active, list_prompts, upsert, set_active)<br>`_load_default_prompts()`@19<br>`_utc()`@41<br>`get_system_prompt_store()`@207<br>`active_system_prompt()`@215 | Database-backed system prompts for OM chat orchestration. |

### API — FastAPI surface

**13 files · 6285 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/api/auth_routes.py` | 287 | `RegisterRequest`<br>`LoginRequest`<br>`_store()`@43<br>`_register_allowed()`@49<br>`_client_ip()`@58<br>`_check_auth_rate()`@62<br>`_bearer_or_cookie()`@78<br>`_audit_auth()`@88 | Account register / login / logout / me API (cookie + Bearer). |
| `om_ai/api/conversations.py` | 449 | `CreateConversationRequest`<br>`UpdateConversationRequest`<br>`AppendMessagesRequest`<br>`CreateFolderRequest`<br>`RenameFolderRequest`<br>`ProfileUpdateRequest`<br>`ConversationFeedbackRequest`<br>`bind_conversation_store()`@18<br>`get_store()`@23<br>`get_bound_conversation_store()`@32<br>`list_conversations()`@86<br>`create_conversation()`@113<br>`get_conversation()`@138 | Conversation / folder / profile REST API for the OM AI chat UI. |
| `om_ai/api/deps.py` | 23 | `require_auth()`@9<br>`require_permission()`@13 | FastAPI auth dependencies (requires fastapi). |
| `om_ai/api/foundation_routes.py` | 120 | `ReasonRequest`<br>`SearchRequest`<br>`UploadPathRequest`<br>`FeedbackRequest`<br>`EvalRequest`<br>`knowledge_search()`@44<br>`knowledge_upload()`@55<br>`reasoning_analyze()`@73<br>`evaluation_run()`@88<br>`learning_feedback()`@99<br>`learning_export()`@115 | Foundation APIs: knowledge, reasoning, evaluation, learning. |
| `om_ai/api/main.py` | 1168 | `LoadRequest`<br>`GenerateRequest`<br>`ChatMessage`<br>`ChatRequest`<br>`MemoryRequest`<br>`KnowledgeAddRequest`<br>`KnowledgeIngestRequest`<br>`GoalRequest`<br>`FeedbackRequest`<br>`MultimodalRequest`<br>`CreateTokenRequest`<br>`favicon()`@94<br>`_print_native_ready_banner()`@188<br>`_audit()`@286<br>`_rate_limit_middleware()`@312<br>`health()`@414<br>`ready()`@469 | OM AI Operating Brain — Production FastAPI application (v0.3.0). |
| `om_ai/api/oi_routes.py` | 50 | `CycleRequest`<br>`HardwareCommand`<br>`SensorIngest`<br>`oi_status()`@32<br>`oi_cycle()`@37<br>`oi_hardware()`@43<br>`oi_sensors()`@49 | Operating Intelligence API — capability board + Observe→Improve cycle. |
| `om_ai/api/onboarding.py` | 249 | `bootstrap_user_workspace()`@74 | First-login workspace bootstrap — defaults for every new OM user. |
| `om_ai/api/openai_compat.py` | 591 | `ChatMessage`<br>`ChatCompletionsRequest`<br>`CompletionsRequest`<br>`bind_engine()`@39<br>`_local_loaded()`@50<br>`_native_ready()`@54<br>`_try_load_native()`@59<br>`_require_local_engine()`@74<br>`_force_tools_from_request()`@113 | OpenAI-compatible API shim for OpenClaw / OpenAI SDK clients. |
| `om_ai/api/platform_routes.py` | 872 | `WorkspaceCreate`<br>`FileCreate`<br>`FileRename`<br>`LibraryCreate`<br>`PromptCreate`<br>`PromptUpdate`<br>`TaskCreate`<br>`TaskUpdate`<br>`MemoryCreate`<br>`MemoryUpdate`<br>`KnowledgeCreate`<br>`SettingsPatch`<br>`AssistantUpdate`<br>`ProjectUpdate`<br>`ToolPatch`<br>`ScheduledTaskCreate`<br>`MemberCreate`<br>`InstructionVersionCreate`<br>`FavoritePatch`<br>`list_workspaces()`@120<br>`create_workspace()`@126<br>`bootstrap_workspace()`@133<br>`global_search()`@150<br>`list_files()`@238<br>`create_file()`@251 | Platform APIs: workspaces, search, files, library, prompts, tasks, memory, settings, explore. |
| `om_ai/api/platform_store.py` | 1520 | `PlatformStore` (__init__, _migrate_tasks, _seed_tools, _seed_explore, list_workspaces, create_workspace, list_files, get_file)<br>`_utc()`@14<br>`get_platform_store()`@1514 | Production platform store: workspaces, files, library, prompts, tasks, settings, knowledge sources. |
| `om_ai/api/workspace_routes.py` | 581 | `ProjectCreate`<br>`ProjectUpdate`<br>`AssistantCreate`<br>`AssistantUpdate`<br>`ProjectChatCreate`<br>`ProjectFileCreate`<br>`ProjectMemoryCreate`<br>`ProjectKnowledgeCreate`<br>`SystemPromptUpsert`<br>`_enrich_project()`@68<br>`_get_owned_project()`@110<br>`list_projects()`@122<br>`get_project()`@147<br>`create_project()`@154<br>`update_project()`@186 | Projects & assistants workspace APIs. |
| `om_ai/api/workspace_store.py` | 375 | `WorkspaceStore` (__init__, _migrate_projects, list_projects, get_project, create_project, delete_project, list_assistants, create_assistant)<br>`_utc()`@14<br>`get_workspace_store()`@369 | Lightweight workspace entities: projects & assistants (SQLite). |

### Backends — OM native load

**6 files · 743 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/backends/base.py` | 27 | `NativeCheckpointError` (__init__)<br>`ModelBackend` (generate, chat, stream_chat, health, model_info) | — |
| `om_ai/backends/checkpoint_checker.py` | 144 | `_repo_root()`@14<br>`verify_file()`@18<br>`validate_metadata()`@39<br>`load_test()`@53<br>`check_checkpoint()`@83<br>`format_model_status()`@127 | OM-1.0 checkpoint verification — non-fatal for serve bootstrap. |
| `om_ai/backends/om_native.py` | 334 | `OMNativeBackend` (__init__, loaded, load, ensure_loaded, generate, chat, stream_chat, health)<br>`pick_device()`@21<br>`default_native_paths()`@43<br>`try_load_native_from_env()`@318 | — |
| `om_ai/backends/om_registry.py` | 181 | `repo_root()`@16<br>`registry_dir()`@20<br>`pick_best_checkpoint()`@24<br>`_checkpoint_loadable()`@38<br>`stamp_tokenizer_binding()`@48<br>`sync_om10_registry()`@77 | OM-1.0 model registry under ``artifacts/models/om-1.0/`` (truthful metadata only). |
| `om_ai/backends/stubs.py` | 53 | `LiveKnowledgeBackend` (retrieve)<br>`ToolRouter` (list_tools, call)<br>`MCPBridge` (connect)<br>`resolve_live_knowledge()`@37<br>`resolve_tool_surface()`@44 | Protocol aliases for OM backends — point at real modules (not unfinished work). |

### Cognitive — OMCognitiveBrain

**11 files · 1677 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/cognitive/__init__.py` | 142 | — | OM Cognitive Intelligence Layer. |
| `om_ai/core/cognitive/agent_collaboration.py` | 28 | `AgentCollaboration` (route) | — |
| `om_ai/core/cognitive/brain_pipeline.py` | 1261 | `OMCognitiveBrain` (__init__, _plan_list, _context_blob, generate, _native_or_fallback_answer, _store_long_context_turn, _safe_fallback, process) | OM-1.0 Cognitive Brain — STEPs 83–93 roadmap orchestration. |
| `om_ai/core/cognitive/cognitive_engine.py` | 83 | `CognitiveEngine` (__init__, process) | — |
| `om_ai/core/cognitive/context_manager.py` | 6 | `ContextManager` (manage) | Context manager stub used by cognitive package exports. |
| `om_ai/core/cognitive/decision_engine.py` | 6 | `DecisionEngine` (decide) | Decision stub used by cognitive package exports. |
| `om_ai/core/cognitive/intelligence_state.py` | 10 | `IntelligenceState` (__init__, update) | Intelligence state stub used by cognitive package exports. |
| `om_ai/core/cognitive/planner.py` | 36 | `PlanningEngine` (create_plan) | — |
| `om_ai/core/cognitive/reasoning_engine.py` | 36 | `ReasoningEngine` (analyze, execute) | — |
| `om_ai/core/cognitive/response_engine.py` | 43 | `ResponseEngine` (analyze_response_style, format) | — |
| `om_ai/core/cognitive/self_evaluator.py` | 26 | `SelfEvaluator` (evaluate) | — |

### Conversation Intelligence

**5 files · 180 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/conversation_intelligence/__init__.py` | 10 | — | — |
| `om_ai/core/conversation_intelligence/conversation_engine.py` | 47 | `ConversationEngine` (__init__, process) | — |
| `om_ai/core/conversation_intelligence/conversation_patterns.py` | 9 | `ConversationPattern` | — |
| `om_ai/core/conversation_intelligence/conversation_router.py` | 52 | `ConversationRouter` (detect) | — |
| `om_ai/core/conversation_intelligence/social_response.py` | 62 | `SocialResponseEngine` (respond) | — |

### Core Observability

**17 files · 812 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/observability/__init__.py` | 60 | — | — |
| `om_ai/core/observability/activity_event.py` | 72 | `ActivityEvent` (to_dict) | — |
| `om_ai/core/observability/activity_formatter.py` | 46 | `ActivityFormatter` (format) | — |
| `om_ai/core/observability/activity_generator.py` | 114 | `ActivityGenerator` (searching, reading_files, knowledge_lookup, research_started, response_ready) | — |
| `om_ai/core/observability/activity_stream.py` | 40 | `ActivityStream` (__init__, subscribe, publish) | — |
| `om_ai/core/observability/activity_types.py` | 30 | `ActivityType` | — |
| `om_ai/core/observability/event.py` | 30 | `ActivityEvent` | — |
| `om_ai/core/observability/event_bus.py` | 28 | `EventBus` (__init__, subscribe, publish) | — |
| `om_ai/core/observability/event_types.py` | 28 | `ActivityType` | — |
| `om_ai/core/observability/metrics.py` | 25 | `AIMetrics` (__init__, increase, get) | — |
| `om_ai/core/observability/observability_engine.py` | 44 | `ObservabilityEngine` (__init__, start_trace, log) | — |
| `om_ai/core/observability/timeline_builder.py` | 69 | `TimelineBuilder` (build, icon) | — |
| `om_ai/core/observability/trace_context.py` | 30 | `TraceContext` (__init__, add, all) | — |
| `om_ai/core/observability/trace_manager.py` | 36 | `TraceManager` (__init__, create, record) | — |
| `om_ai/core/observability/trace_storage.py` | 59 | `TraceStorage` (__init__, save, read_all) | — |
| `om_ai/core/observability/user_activity.py` | 35 | `UserActivity` (add) | — |
| `om_ai/core/observability/websocket_manager.py` | 66 | `WebSocketManager` (__init__, connect, disconnect, broadcast) | — |

### Core Knowledge Brain

**8 files · 367 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/knowledge_brain/__init__.py` | 22 | — | — |
| `om_ai/core/knowledge_brain/knowledge_brain.py` | 58 | `KnowledgeBrain` (__init__, analyze, add) | — |
| `om_ai/core/knowledge_brain/knowledge_confidence.py` | 28 | `KnowledgeConfidence` (calculate) | — |
| `om_ai/core/knowledge_brain/knowledge_context.py` | 28 | `KnowledgeContext` | — |
| `om_ai/core/knowledge_brain/knowledge_ingestion.py` | 40 | `KnowledgeIngestion` (__init__, ingest) | — |
| `om_ai/core/knowledge_brain/knowledge_memory.py` | 59 | `KnowledgeMemory` (__init__, store, retrieve, search, all) | — |
| `om_ai/core/knowledge_brain/knowledge_router.py` | 106 | `KnowledgeRouter` (__init__, route) | — |
| `om_ai/core/knowledge_brain/knowledge_sync.py` | 26 | `KnowledgeSync` (sync) | — |

### Research Intelligence

**8 files · 182 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/research_intelligence/__init__.py` | 22 | — | — |
| `om_ai/core/research_intelligence/evidence.py` | 12 | `Evidence` | — |
| `om_ai/core/research_intelligence/evidence_validator.py` | 18 | `EvidenceValidator` (validate) | — |
| `om_ai/core/research_intelligence/research_agent.py` | 21 | `ResearchAgent` (create_task) | — |
| `om_ai/core/research_intelligence/research_engine.py` | 39 | `ResearchEngine` (__init__, create) | — |
| `om_ai/core/research_intelligence/research_memory.py` | 23 | `ResearchMemory` (__init__, add, all) | — |
| `om_ai/core/research_intelligence/research_pipeline.py` | 35 | `ResearchPipeline` (__init__, run) | — |
| `om_ai/core/research_intelligence/research_task.py` | 12 | `ResearchTask` | — |

### Long Context

**8 files · 252 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/long_context/context_manager.py` | 50 | `ContextManager` (__init__, remember, get_context) | — |
| `om_ai/core/long_context/context_memory.py` | 42 | `ContextMemory` (__init__, add, all, clear) | — |
| `om_ai/core/long_context/context_ranker.py` | 22 | `ContextRanker` (rank) | — |
| `om_ai/core/long_context/context_retriever.py` | 36 | `ContextRetriever` (search) | — |
| `om_ai/core/long_context/context_window.py` | 25 | `ContextWindow` (__init__, compress) | — |
| `om_ai/core/long_context/conversation_state.py` | 25 | `ConversationState` | — |
| `om_ai/core/long_context/long_context_engine.py` | 49 | `LongContextEngine` (__init__, process, store) | — |

### Advanced Reasoning

**8 files · 227 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/advanced_reasoning/__init__.py` | 9 | — | — |
| `om_ai/core/advanced_reasoning/decomposition_engine.py` | 22 | `DecompositionEngine` (split) | — |
| `om_ai/core/advanced_reasoning/planning_engine.py` | 23 | `PlanningEngine` (create_plan) | — |
| `om_ai/core/advanced_reasoning/problem_analyzer.py` | 26 | `ProblemAnalyzer` (analyze) | — |
| `om_ai/core/advanced_reasoning/reasoning_engine.py` | 79 | `ReasoningEngine` (__init__, reason, verify) | — |
| `om_ai/core/advanced_reasoning/reasoning_memory.py` | 23 | `ReasoningMemory` (__init__, store, history) | — |
| `om_ai/core/advanced_reasoning/reasoning_state.py` | 22 | `ReasoningState` | — |
| `om_ai/core/advanced_reasoning/verification_engine.py` | 23 | `VerificationEngine` (verify) | — |

### Production Brain (new)

**2 files · 277 lines**

| Path | Lines | Classes / key APIs | Doc / role |
|------|------:|--------------------|-----------|
| `om_ai/core/brain_runtime/__init__.py` | 10 | — | — |
| `om_ai/core/brain_runtime/production_brain.py` | 267 | `OMProductionBrain` (__init__, process) | — |

---

## 3. `chat_pipeline.py` stage map (826 lines)

| Stage | What it does | Module(s) |
|-------|--------------|-----------|
| language | Detect + response language | `om_ai.language.LanguageManager` |
| multilingual_knowledge | Meaning → retrieval query | `om_ai.language.meaning.MultilingualKnowledge` |
| memory | Advanced memory recall | `om_ai.memory.memory_manager.AdvancedMemorySystem` |
| intent | Understanding + intent | `core.intelligence.UnderstandingEngine`, `IntentEngine` |
| tool_decision | Context intent / tools | `core.understanding.context_intent` |
| live_knowledge | Web/Wikipedia grounded draft | `runtime.live_answer` |
| action / tools | Tool plan + execute | `tools.intelligence`, `tools.chat_runner` |
| knowledge_brain | **AdvancedKnowledgeBrain** (different from core KB) | `om_ai.knowledge.brain` |
| reasoning | `run_reasoning_pipeline` | `core.reasoning.pipeline` |
| model | Native chat with internal context | `chat_orchestrator.build_chat_messages` |
| language check / final | Sanitize + memory write | `public_reply`, advanced memory |

Gate: `OM_CHAT_PIPELINE` (default **on**).

---

## 4. `brain_pipeline.py` stage map (~1235+ lines)

Class: `OMCognitiveBrain`

| Stage | Integration |
|-------|-------------|
| language | `detect_language` |
| conversation_intelligence | `ConversationEngine.process` → early social reply |
| knowledge_brain | `KnowledgeBrain.analyze` |
| research_pipeline | if `not knowledge_found` → `ResearchPipeline.run` |
| understanding / freshness / research | UnderstandingEngine + FreshnessDetector + ResearchEngine |
| roadmap_enrich | STEPs 83–93 `OMRoadmapStack` |
| reasoning | `core.reasoning.ReasoningEngine.process` |
| coding_intelligence | CodingIntelligence when coding intent |
| response_engine / context_intelligence | prepare + filter |
| long_context | `LongContextEngine.process` before model |
| advanced_reasoning | `AdvancedReasoningEngine.reason` before model |
| om_native_model | `_native_or_fallback_answer` |
| leakage / garbage / quality / retries | quality loop |
| roadmap_learn | learn_after_answer |
| long_context_store | store user + assistant turns |

Methods: `__init__`, `generate`, `process`, `_native_or_fallback_answer`, `_store_long_context_turn`, `_safe_fallback`.

**Gap:** `run_cognitive_brain` calls `.process()`, not `.generate()` — long_context / KB / conversation integrations on `generate` are skipped on that fallback path.

---

## 5. Duplicate / overlapping modules

| Concept | Locations |
|---------|-----------|
| KnowledgeBrain | `om_ai/core/knowledge_brain/` vs `om_ai/knowledge/brain.py` (AdvancedKnowledgeBrain) vs `om_ai/knowledge_brain/` |
| ReasoningEngine | `core/reasoning/`, `core/advanced_reasoning/`, `core/cognitive/reasoning_engine.py` (stub), `om_ai/reasoning/` |
| ResponseEngine | `core/response/`, `core/cognitive/response_engine.py` (stub) |
| Observability | `om_ai/core/observability/` vs `om_ai/observability/` |
| Conversation | `core/conversation_intelligence/` vs `om_ai/conversation_engine/` |
| Research | `core/research/`, `core/research_intelligence/`, `om_ai/research/` |

---

## 6. Repo scale snapshot

- `om_ai/`: **~102k lines**, **~1106** Python files
- Largest: `om_ai/core/` (~28k lines / 394 files), `api/` (~6.3k), `runtime/` (~5.7k), `knowledge/` (~5.5k)
- Many packages under 500 lines are thin scaffolds

---

## 7. Recommended next wiring (to make “full brain” production)

1. Point `run_cognitive_brain` / chat fallback at `OMCognitiveBrain().generate(...)` (or share stages with chat_pipeline).
2. Call `civilization` / `autonomous_research` from `generate` when intent warrants, or remove dead construction.
3. Unify Knowledge Brain: one retrieve API used by both `chat_pipeline` and `brain_pipeline`.
4. Hook `ObservabilityEngine` / `ActivityGenerator` into `chat_pipeline` stages for UI activity stream.
5. Flesh `ResearchPipeline` beyond task stub, or always delegate to `ResearchEngine`.

---

## 8. Quick path cheat-sheet

| Want | Path |
|------|------|
| Serve entry | `om_ai/api/main.py` |
| OpenAI chat | `om_ai/api/openai_compat.py` |
| Backend select | `om_ai/runtime/chat_backend.py` |
| Default pipeline | `om_ai/runtime/chat_pipeline.py` |
| Cognitive brain | `om_ai/core/cognitive/brain_pipeline.py` |
| External LLMs / OpenRouter | `om_ai/runtime/external_llms.py` |
| Native weights | `om_ai/backends/om_native.py` |
| Full structure map | `PROJECT.md` |
