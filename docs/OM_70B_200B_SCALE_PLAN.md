# OM-70B and OM-200B: honest scale-up plan

## Status

This document defines an engineering path, not a claim that these models have been trained.

- `configs/70b.json`: existing native Transformer architecture preset; the repository estimator should be run to confirm the exact count (about 69B under the current estimator).
- `configs/om-2.0-200b.json`: new architecture-only preset, estimated at about 191.7B parameters by `ModelConfig.parameter_estimate()`.
- No trained OM-70B or OM-200B checkpoint is verified by this plan.
- A model's parameter count does not prove reasoning, coding, factuality, alignment, or GPT/Claude-level capability.

## Why the Mac mini is not the training target for 70B/200B

A Mac mini with large unified memory is useful for development, configuration tests, smaller-scale training experiments, and inference experiments. It is not a realistic platform for pretraining a 70B or 200B model from scratch to competitive quality. These scales require a distributed GPU cluster, sharded optimizer state, high-bandwidth GPU interconnect, fast shared storage, failure recovery, and a large legally usable corpus. Even loading quantized weights for inference is a different problem from training all parameters.

Do not try to instantiate the 70B/200B models on the Mac mini just to test the config. Use the parameter estimator and config-only tests. The architecture tests intentionally avoid allocating model weights.

## Build stages

### Stage 0 — Make the native baseline reproducible

1. Verify OM-1.0 config/tokenizer/checkpoint compatibility.
2. Run native-only diagnostics and record checkpoint/tokenizer/config hashes.
3. Keep a frozen baseline and a benchmark report.
4. Ensure the runtime does not silently substitute a third-party model when native OM fails.

### Stage 1 — Validate and train OM-300M, then consider OM-1B

1. Run config-only model-info and architecture tests.
2. Run a tiny forward/backward/checkpoint smoke test on MPS.
3. Build a licensed, deduplicated pretraining corpus with a held-out validation split.
4. Measure tokens/sec, memory, validation loss, and checkpoint recovery on the actual Mac.
5. Train from random initialization only after the data and training pipeline are validated.
6. Instruction-tune with diverse, verified examples; preference-optimize only with vetted preference pairs.
7. Evaluate against fixed held-out tasks and retain the previous model unless the new model demonstrably improves quality.

### Stage 2 — Distributed OM-70B

Before any expensive job, provide:
- GPU model/count and usable VRAM per GPU
- Interconnect and node topology
- Storage capacity and throughput
- Licensed corpus inventory and token count
- Training budget and checkpoint/restart plan
- Validation suite and explicit promotion thresholds

Use distributed sharding (for example, FSDP or DeepSpeed ZeRO-3) and run a multi-GPU preflight first. The existing launcher is infrastructure only; a successful launcher invocation is not proof that training completed or that the model is capable. Require a real checkpoint, training logs, validation curves, and benchmark reports.

### Stage 3 — Distributed OM-200B

The 200B preset is a future architecture target, not the next Mac mini training job. Before launching:
- validate the implementation at smaller scales;
- estimate parameter, optimizer, activation, KV-cache, and checkpoint memory with the exact training recipe;
- establish multi-node fault recovery and storage bandwidth;
- verify dataset rights, deduplication, contamination controls, and validation isolation;
- run a short distributed scaling test and extrapolate throughput/cost;
- pretrain, instruction-tune, and align with curated data;
- publish benchmark methodology, limitations, hardware, data provenance, and checkpoint hashes.

Do not assume the 70B architecture can be turned into a 200B model by changing one number and resuming its checkpoint. The shapes differ; a new architecture requires compatible new weights or a deliberate, tested conversion strategy.

## Product architecture

- Native OM remains the default brain and uses OM-owned checkpoints.
- The model runtime fails clearly if the selected native checkpoint cannot load; it must not silently fall back to Qwen, Claude, GPT, or another provider.
- Retrieval, memory, search, and tools may improve product usefulness, but they do not substitute for learned model capability.
- Third-party models may be explicitly selected for comparison or research, never silently used as OM's default.
- Promote a checkpoint only after reproducible evaluation and reliability/safety gates pass.

## Capability claims

Do not claim GPT-5, Claude, or frontier parity based on parameter count, training loss, synthetic benchmark scores, or a successful training process. Any comparison must use a documented, contamination-controlled benchmark suite, equivalent evaluation conditions, error analysis, and reproducible results.
