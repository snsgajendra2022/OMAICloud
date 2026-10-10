# OM Architecture Audit (generated)

- Python files scanned: **1880**
- Static parse errors: **0**
- Generation-like function definitions: **60**
- Generation-like call sites: **96**
- Static import-cycle groups: **7**

> Static inventory only. It is not a runtime trace and does not establish model quality.

## Generation-like function definitions

| File | Line | Function | Async |
|---|---:|---|---|
| om_ai/agents/orchestrator.py | 549 | generate | False |
| om_ai/api/foundation_routes.py | 271 | generate | False |
| om_ai/api/main.py | 605 | generate | False |
| om_ai/api/main.py | 670 | chat | False |
| om_ai/backends/base.py | 17 | generate | False |
| om_ai/backends/base.py | 19 | chat | False |
| om_ai/backends/om_native.py | 199 | generate | False |
| om_ai/backends/om_native.py | 203 | chat | False |
| om_ai/cli.py | 538 | generate | False |
| om_ai/cli.py | 552 | chat | False |
| om_ai/core/advanced_learning/dataset_generator.py | 5 | generate | False |
| om_ai/core/chat_intelligence/hypothesis_engine.py | 60 | generate | False |
| om_ai/core/cognitive/brain_pipeline.py | 1690 | generate | False |
| om_ai/core/companion_brain/response_engine.py | 11 | generate | False |
| om_ai/core/dialogue_intelligence/question_generator.py | 8 | generate | False |
| om_ai/core/distillation/curriculum_generator.py | 101 | generate | False |
| om_ai/core/distillation/ollama_client.py | 39 | generate | False |
| om_ai/core/model_runtime/model_gateway.py | 176 | generate | False |
| om_ai/core/model_runtime/model_gateway.py | 268 | chat | False |
| om_ai/core/onboarding/prompt_generator.py | 40 | generate | False |
| om_ai/core/response/answer_generator.py | 36 | generate | False |
| om_ai/core/self_evaluation/improvement_feedback.py | 12 | generate | False |
| om_ai/core/voice_engine/realtime_tts.py | 52 | stream | False |
| om_ai/data_engine/benchmark/report.py | 13 | generate | False |
| om_ai/data_engine/connectors/base.py | 18 | stream | False |
| om_ai/data_engine/connectors/github_code.py | 28 | stream | False |
| om_ai/data_engine/connectors/huggingface.py | 30 | stream | False |
| om_ai/data_engine/connectors/wikipedia.py | 27 | stream | False |
| om_ai/data_engine/curriculum/training_plan.py | 15 | generate | False |
| om_ai/generation/engine.py | 10 | generate | False |
| om_ai/improvement/generator.py | 19 | generate | False |
| om_ai/model/causal_loss.py | 30 | forward | False |
| om_ai/model/embeddings.py | 17 | forward | False |
| om_ai/model/transformer.py | 27 | forward | False |
| om_ai/model/transformer.py | 48 | forward | False |
| om_ai/model/transformer.py | 82 | forward | False |
| om_ai/model/transformer.py | 136 | forward | False |
| om_ai/model/transformer.py | 160 | forward | False |
| om_ai/model/transformer.py | 270 | forward | False |
| om_ai/model/transformer.py | 355 | generate | False |
| om_ai/recovery/strategy.py | 11 | generate | False |
| om_ai/runtime/chat_backend.py | 1205 | chat_reply | False |
| om_ai/runtime/chat_pipeline.py | 42 | run_chat_pipeline | False |
| om_ai/runtime/engine.py | 473 | generate | False |
| om_ai/runtime/engine.py | 605 | chat | False |
| om_ai/runtime/model_gateway.py | 46 | generate | False |
| om_ai/runtime/model_gateway.py | 60 | chat | False |
| om_ai/self_improvement/strategy.py | 10 | generate | False |
| om_ai/testing/generator.py | 10 | generate | False |
| om_ai/training/ppo.py | 196 | forward | False |
| om_ai/training/reward_model.py | 14 | forward | False |
| om_ai/vision/multimodal.py | 8 | forward | False |
| om_ai/vision/multimodal.py | 14 | forward | False |
| om_ai/vision/multimodal.py | 17 | generate | False |
| om_ai/vision/vit.py | 16 | forward | False |
| om_ai/voice/audio_encoder.py | 7 | forward | False |
| om_ai/voice/audio_encoder.py | 17 | forward | False |
| om_ai/voice/audio_encoder.py | 21 | forward | False |
| om_ai/voice/text_to_speech.py | 15 | generate | False |
| om_ai/workflow/generator.py | 18 | generate | False |

## Generation-like call sites

| File | Line | Callee |
|---|---:|---|
| om_ai/agents/orchestrator.py | 389 | self._llm.generate |
| om_ai/agents/orchestrator.py | 429 | self._llm.generate |
| om_ai/agents/orchestrator.py | 551 | self._engine.generate |
| om_ai/api/companion/routes.py | 264 | response_engine.generate |
| om_ai/api/foundation_routes.py | 272 | gateway.generate |
| om_ai/api/main.py | 611 | model_gateway.generate |
| om_ai/api/main.py | 679 | chat_reply |
| om_ai/api/main.py | 1199 | model_gateway.generate |
| om_ai/api/openai_compat.py | 309 | chat_reply |
| om_ai/api/openai_compat.py | 561 | eng.generate |
| om_ai/backends/om_native.py | 201 | self.engine.generate |
| om_ai/backends/om_native.py | 205 | self.engine.chat |
| om_ai/backends/om_native.py | 210 | self.engine.generate_stream |
| om_ai/backends/om_native.py | 217 | self.engine.chat |
| om_ai/backends/om_native.py | 244 | self.engine.model.generate_stream |
| om_ai/cli.py | 541 | eng.generate |
| om_ai/cli.py | 558 | eng.chat |
| om_ai/cli_commands/distill_commands.py | 147 | generate |
| om_ai/cli_commands/distill_commands.py | 323 | generate |
| om_ai/core/advanced_learning/advanced_learning_engine.py | 48 | self.dataset.generate |
| om_ai/core/brain_runtime/production_brain.py | 934 | self.chat_quality_engine.improve |
| om_ai/core/chat_intelligence/hypothesis_engine.py | 109 | self.reasoning_engine.generate_hypothesis |
| om_ai/core/chat_intelligence/solution_engine.py | 78 | self.hypothesis_engine.generate |
| om_ai/core/cognitive/brain_pipeline.py | 2347 | backend.chat |
| om_ai/core/cognitive/brain_pipeline.py | 2389 | self.generator.generate |
| om_ai/core/cognitive/brain_pipeline.py | 2597 | self.generate |
| om_ai/core/companion_architecture/companion_pipeline.py | 278 | generate |
| om_ai/core/companion_architecture/companion_pipeline.py | 281 | generate |
| om_ai/core/companion_brain/companion_runtime.py | 336 | self.response.generate |
| om_ai/core/companion_personality/voice_presence.py | 271 | response_engine.generate |
| om_ai/core/companion_personality/voice_presence.py | 327 | chat_reply |
| om_ai/core/companion_runtime/companion_runtime.py | 1348 | chat_reply |
| om_ai/core/dialogue_intelligence/dialogue_manager.py | 35 | self.questions.generate |
| om_ai/core/distillation/continuous_loop.py | 66 | self.curriculum.generate |
| om_ai/core/distillation/curriculum_generator.py | 165 | self.generate |
| om_ai/core/distillation/llm_harvester.py | 217 | chat |
| om_ai/core/distillation/teacher_manager.py | 242 | self.client.generate |
| om_ai/core/evaluation_system/__init__.py | 38 | generate |
| om_ai/core/human_companion/response/__init__.py | 40 | generate |
| om_ai/core/human_companion/response/__init__.py | 43 | generate |
| om_ai/core/human_companion/response/__init__.py | 56 | generate |
| om_ai/core/human_intelligence/human_conversation_pipeline.py | 173 | generate |
| om_ai/core/human_intelligence/human_conversation_pipeline.py | 176 | generate |
| om_ai/core/intelligence/real_answer.py | 371 | backend.generate |
| om_ai/core/learning/learning_scheduler.py | 90 | generate |
| om_ai/core/machine_learning/evaluation/evaluation_engine.py | 38 | generate |
| om_ai/core/model_improvement/model_benchmark.py | 22 | generate |
| om_ai/core/model_runtime/model_gateway.py | 160 | self.generate |
| om_ai/core/model_runtime/model_gateway.py | 294 | backend.chat |
| om_ai/core/model_runtime/model_gateway.py | 360 | backend.generate |
| om_ai/core/model_runtime/model_gateway.py | 363 | backend.generate |
| om_ai/core/model_runtime/model_gateway.py | 369 | backend.chat |
| om_ai/core/model_runtime/model_gateway.py | 372 | backend.chat |
| om_ai/core/model_runtime/model_loader.py | 105 | backend.generate |
| om_ai/core/onboarding/onboarding_engine.py | 153 | self.prompts.generate |
| om_ai/core/reasoning/solver.py | 181 | backend.generate |
| om_ai/core/self_evaluation/self_evaluation_engine.py | 83 | self.feedback.generate |
| om_ai/core/steps/step84_advanced_learning.py | 103 | self.generate_dataset |
| om_ai/core/voice_engine/tts_provider.py | 210 | self.realtime.stream |
| om_ai/core/voice_intelligence/speech_synthesizer.py | 182 | generate |
| om_ai/data_engine/factory.py | 60 | connector.stream |
| om_ai/eval/benchmarks.py | 30 | self.model.generate |
| om_ai/eval/chatgpt_compare.py | 118 | run_chat_pipeline |
| om_ai/improvement/quality.py | 60 | self.generator.generate |
| om_ai/model/transformer.py | 377 | self.forward |
| om_ai/model/transformer.py | 404 | self.forward |
| om_ai/model/transformer.py | 437 | self.forward |
| om_ai/model/transformer.py | 465 | self.forward |
| om_ai/model/transformer.py | 491 | self.generate |
| om_ai/multimodal/orchestrator.py | 209 | self._llm.generate_with_context |
| om_ai/multimodal/orchestrator.py | 216 | self._llm.generate |
| om_ai/operating_intelligence/universal.py | 122 | self.generation.generate |
| om_ai/recovery/executor.py | 81 | self.strategy.generate |
| om_ai/runtime/chat_backend.py | 523 | run_chat_pipeline |
| om_ai/runtime/chat_orchestrator.py | 26 | brain.generate |
| om_ai/runtime/connectivity_bridge.py | 413 | generate |
| om_ai/runtime/engine.py | 490 | self.model.generate |
| om_ai/runtime/engine.py | 522 | self.model.generate_stream |
| om_ai/runtime/engine.py | 579 | self.model.generate |
| om_ai/runtime/engine.py | 653 | self.generate |
| om_ai/runtime/engine.py | 672 | self.generate |
| om_ai/runtime/model_gateway.py | 52 | self.backend.generate |
| om_ai/runtime/model_gateway.py | 66 | self.backend.chat |
| om_ai/runtime/model_gateway.py | 79 | self.backend.generate_stream |
| om_ai/self_improvement/engine.py | 66 | self.strategy.generate |
| om_ai/software_agent/agent.py | 93 | self.modifier.generate_change |
| om_ai/testing/agent.py | 51 | self.generator.generate |
| om_ai/vision/multimodal.py | 18 | self.llm.generate |
| om_ai/voice/__init__.py | 51 | run_chat_pipeline |
| scripts/acceptance_test.py | 108 | eng.generate_with_context |
| scripts/auto_harvest_train_om.py | 95 | gen.generate |
| scripts/certify_om_release.py | 135 | backend.generate |
| scripts/diagnose_native_chat.py | 112 | backend.chat |
| scripts/evaluate_om_capabilities.py | 161 | backend.chat |
| scripts/evaluate_om_capabilities.py | 194 | backend.chat |
| scripts/smoke_test.py | 17 | model.generate |

## Static import cycles

- om_ai.agent -> om_ai.agent.brain -> om_ai.agent.coding_agent -> om_ai.agent.executor -> om_ai.agent.verifier -> om_ai.backends.om_native -> om_ai.coding_brain -> om_ai.core.cognitive.brain_pipeline -> om_ai.core.intelligence.real_answer -> om_ai.core.reasoning.pipeline -> om_ai.core.reasoning.reflection -> om_ai.core.reasoning.solver -> om_ai.core.reasoning.verifier -> om_ai.core.response.intelligence -> om_ai.core.response.quality -> om_ai.core.response.response_formatter -> om_ai.improvement -> om_ai.learning -> om_ai.operating_intelligence.universal -> om_ai.reasoning.engine -> om_ai.runtime.chat_backend -> om_ai.runtime.chat_orchestrator -> om_ai.runtime.chat_pipeline -> om_ai.runtime.connectivity_bridge -> om_ai.runtime.engine -> om_ai.software_agent -> om_ai.testing -> om_ai.tools.chat_runner
- om_ai.api.auth_routes -> om_ai.api.main
- om_ai.core -> om_ai.core.intelligence -> om_ai.core.intent_engine -> om_ai.core.reasoning -> om_ai.core.response
- om_ai.core.presence_engine -> om_ai.core.presence_runtime
- om_ai.security.accounts -> om_ai.security.auth -> om_ai.security.tokens
- om_ai.tools -> om_ai.tools.intelligence
- om_ai.training.chatgpt_upgrade -> om_ai.training.dpo -> om_ai.training.production_pipeline -> om_ai.training.sft

## Parse errors

None.

## Tokenizer-related files

- om_ai/api/auth_routes.py
- om_ai/api/companion/routes.py
- om_ai/api/foundation_routes.py
- om_ai/api/main.py
- om_ai/api/openai_compat.py
- om_ai/api/platform_routes.py
- om_ai/api/platform_store.py
- om_ai/api/workspace_routes.py
- om_ai/backends/checkpoint_checker.py
- om_ai/backends/om_native.py
- om_ai/backends/om_registry.py
- om_ai/brain/dataset_engine.py
- om_ai/checkpoint/bundle.py
- om_ai/cli.py
- om_ai/continuous/cycle.py
- om_ai/conversation_engine/topic_tracker.py
- om_ai/core/chat_intelligence/response_optimizer.py
- om_ai/core/chat_intelligence/safety_filter.py
- om_ai/core/companion_memory/memory_service.py
- om_ai/core/companion_runtime/companion_runtime.py
- om_ai/core/config.py
- om_ai/core/dataset_intelligence/duplicate_detector.py
- om_ai/core/device_runtime/file_controller.py
- om_ai/core/device_runtime/weather.py
- om_ai/core/distillation/dataset_builder.py
- om_ai/core/distillation/knowledge_extractor.py
- om_ai/core/distillation/provenance_manager.py
- om_ai/core/intelligence_dataset/deduplicator.py
- om_ai/core/intelligence_dataset/embedding_provider.py
- om_ai/core/machine_learning/data/dataset_manager.py
- om_ai/core/machine_learning/feedback/feedback_collector.py
- om_ai/core/model_runtime/checkpoint_loader.py
- om_ai/core/model_runtime/model_bundle.py
- om_ai/core/model_runtime/model_gateway.py
- om_ai/core/model_runtime/model_loader.py
- om_ai/core/model_runtime/observability.py
- om_ai/core/model_runtime/production_tokenizer.py
- om_ai/core/model_runtime/quality_gate.py
- om_ai/core/research/page_reader.py
- om_ai/core/response/garbage_detector.py
- om_ai/core/response/quality_checker.py
- om_ai/core/training_intelligence/curriculum_engine.py
- om_ai/core/training_intelligence/knowledge_sampler.py
- om_ai/core/voice_engine/realtime_tts.py
- om_ai/core/voice_engine/voice_model.py
- om_ai/corpus/omai_v1.py
- om_ai/corpus/service.py
- om_ai/data/pipeline.py
- om_ai/data_engine/continuous/deduplicator.py
- om_ai/data_engine/pipeline/deduplicator.py
- om_ai/data_pipeline/__init__.py
- om_ai/data_pipeline/deduplicator.py
- om_ai/data_pipeline/pipeline.py
- om_ai/data_pipeline/tokenizer.py
- om_ai/data_pipeline/validator.py
- om_ai/desktop/companion_window.py
- om_ai/diagnostics/system_check.py
- om_ai/discovery/project.py
- om_ai/eval/benchmarks.py
- om_ai/foundation/__init__.py
- om_ai/genesis/generator.py
- om_ai/improvement/trainer_queue.py
- om_ai/knowledge/context_filter.py
- om_ai/knowledge/embeddings.py
- om_ai/knowledge/ingestion/__init__.py
- om_ai/knowledge/processing/embedder.py
- om_ai/knowledge/rag.py
- om_ai/knowledge/retrieval/keyword_search.py
- om_ai/knowledge/retrieval/vector_retriever.py
- om_ai/knowledge_brain/corpus.py
- om_ai/knowledge_brain/eras.py
- om_ai/live_knowledge/crawler.py
- om_ai/live_knowledge/web_search.py
- om_ai/memory/sqlite_memory.py
- om_ai/model/embeddings.py
- om_ai/model/transformer.py
- om_ai/multimodal/document_engine.py
- om_ai/multimodal/image_engine.py
- om_ai/multimodal/orchestrator.py
- om_ai/observability/metrics.py
- om_ai/operating_intelligence/neural_simulation.py
- om_ai/operating_intelligence/perception_bridge.py
- om_ai/reasoning/planner.py
- om_ai/registry/model_registry.py
- om_ai/runtime/chat_orchestrator.py
- om_ai/runtime/chat_pipeline.py
- om_ai/runtime/engine.py
- om_ai/runtime/model_gateway.py
- om_ai/runtime/observability.py
- om_ai/security/accounts.py
- om_ai/security/audit.py
- om_ai/security/audit_log.py
- om_ai/security/tokens.py
- om_ai/tokenizer/__init__.py
- om_ai/tokenizer/byte_bpe.py
- om_ai/tokenizer/loader.py
- om_ai/tokenizer/omai_v1.py
- om_ai/training/__init__.py
- om_ai/training/chatgpt_upgrade.py
- om_ai/training/deepspeed_train.py
- om_ai/training/distributed.py
- om_ai/training/fix_and_check_om70b_mac.py
- om_ai/training/local_knowledge.py
- om_ai/training/om_tokenizer.py
- om_ai/training/ppo.py
- om_ai/training/preference.py
- om_ai/training/preflight.py
- om_ai/training/production_pipeline.py
- om_ai/training/sft.py
- om_ai/training/train_70b.py
- om_ai/training/train_om1.py
- om_ai/training/trainer.py
- om_ai/vision/__init__.py
- om_ai/vision/base.py
- om_ai/vision/multimodal.py
- om_ai/vision/vit.py
- om_ai/voice/audio_encoder.py
- scripts/acceptance_test.py
- scripts/acquire_fineweb.py
- scripts/audit_om_architecture.py
- scripts/auto_harvest_train_om.py
- scripts/build_chat_sft_v4.py
- scripts/certify_om.py
- scripts/certify_om_release.py
- scripts/diagnose_native_chat.py
- scripts/evaluate_om_capabilities.py
- scripts/om70b_preflight.py
- scripts/run_actual_training_pipeline.py
- scripts/smoke_test.py
- scripts/train_production_tokenizer.py

## Checkpoint-related files

- om_ai/api/main.py
- om_ai/api/openai_compat.py
- om_ai/backends/__init__.py
- om_ai/backends/base.py
- om_ai/backends/checkpoint_checker.py
- om_ai/backends/om_native.py
- om_ai/backends/om_registry.py
- om_ai/checkpoint/__init__.py
- om_ai/checkpoint/bundle.py
- om_ai/cli.py
- om_ai/cli_commands/distill_commands.py
- om_ai/code_intelligence/scanner.py
- om_ai/continuous/cycle.py
- om_ai/conversation_engine/topic_tracker.py
- om_ai/core/background_brain/monitoring_engine.py
- om_ai/core/checkpoint_intelligence/__init__.py
- om_ai/core/checkpoint_intelligence/benchmark.py
- om_ai/core/checkpoint_intelligence/checkpoint.py
- om_ai/core/checkpoint_intelligence/checkpoint_manager.py
- om_ai/core/checkpoint_intelligence/checkpoint_validator.py
- om_ai/core/checkpoint_intelligence/rollback_manager.py
- om_ai/core/companion_runtime/companion_runtime.py
- om_ai/core/config.py
- om_ai/core/continuous_improvement/continuous_engine.py
- om_ai/core/conversation_runtime/conversational_flow.py
- om_ai/core/distillation/__init__.py
- om_ai/core/distillation/checkpoint_manager.py
- om_ai/core/distillation/harvest_engine.py
- om_ai/core/machine_learning/learning_engine.py
- om_ai/core/model_improvement/__init__.py
- om_ai/core/model_improvement/checkpoint_selector.py
- om_ai/core/model_improvement/evaluation_engine.py
- om_ai/core/model_improvement/model_improvement_layer.py
- om_ai/core/model_runtime/checkpoint_loader.py
- om_ai/core/model_runtime/model_bundle.py
- om_ai/core/model_runtime/model_gateway.py
- om_ai/core/model_runtime/model_loader.py
- om_ai/core/model_runtime/observability.py
- om_ai/core/steps/step93_model_training.py
- om_ai/core/training_intelligence/training_manager.py
- om_ai/diagnostics/repair.py
- om_ai/diagnostics/system_check.py
- om_ai/foundation/__init__.py
- om_ai/genesis/generator.py
- om_ai/identity/__init__.py
- om_ai/improvement/trainer_queue.py
- om_ai/model/transformer.py
- om_ai/registry/model_registry.py
- om_ai/roadmap.py
- om_ai/runtime/chat_backend.py
- om_ai/runtime/chat_pipeline.py
- om_ai/runtime/engine.py
- om_ai/runtime/model_gateway.py
- om_ai/system/__init__.py
- om_ai/tokenizer/loader.py
- om_ai/training/chatgpt_upgrade.py
- om_ai/training/checkpoint.py
- om_ai/training/deepspeed_train.py
- om_ai/training/distributed.py
- om_ai/training/dpo.py
- om_ai/training/fix_and_check_om70b_mac.py
- om_ai/training/ppo.py
- om_ai/training/production_pipeline.py
- om_ai/training/reward_model.py
- om_ai/training/sft.py
- om_ai/training/train_70b.py
- om_ai/training/train_om1.py
- om_ai/training/trainer.py
- scripts/acceptance_test.py
- scripts/audit_om_architecture.py
- scripts/auto_harvest_train_om.py
- scripts/certify_om.py
- scripts/certify_om_release.py
- scripts/diagnose_native_chat.py
- scripts/evaluate_om_capabilities.py
- scripts/run_actual_training_pipeline.py

## API / CLI / runtime entrypoint markers

- om_ai/agent/useful_reply.py
- om_ai/api/auth_routes.py
- om_ai/api/companion/routes.py
- om_ai/api/conversations.py
- om_ai/api/foundation_routes.py
- om_ai/api/main.py
- om_ai/api/oi_routes.py
- om_ai/api/openai_compat.py
- om_ai/api/platform_routes.py
- om_ai/api/workspace_routes.py
- om_ai/cli.py
- om_ai/eval/chatgpt_compare.py
- om_ai/genesis/generator.py
- om_ai/tools/llm_harvest.py
- om_ai/training/deepspeed_train.py
- om_ai/training/distributed.py
- om_ai/training/local_knowledge.py
- scripts/acceptance_test.py
- scripts/audit_om_architecture.py
- scripts/auto_harvest_train_om.py
- scripts/build_chat_sft_v4.py
- scripts/certify_om.py
- scripts/certify_om_release.py
- scripts/diagnose_native_chat.py
- scripts/evaluate_om_capabilities.py
- scripts/merge_all_sft.py
- scripts/om70b_preflight.py
- scripts/prepare_corpus.py
- scripts/run_actual_training_pipeline.py
- scripts/shard_corpus.py
- scripts/train_production_tokenizer.py

## Limitations

- Static AST scan cannot discover every dynamic import, plugin, reflection, shell-launched process, or runtime-generated call.
- Static import cycles do not prove runtime import failure; runtime smoke tests remain required.
- Tokenizer/checkpoint references are lexical signals; runtime bindings require separate verification.
