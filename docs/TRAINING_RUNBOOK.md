# OM AI Actual Intelligence-Building Runbook

This runbook describes the executable path that turns source code + approved data + compute into owned OM model weights.

## 1. Approve and audit training sources

Edit `data/source_manifest.example.json`. Every source must declare its owner, license, and `allowed_for_training=true`.

```bash
python scripts/prepare_corpus.py \
  --manifest data/source_manifest.example.json \
  --output artifacts/corpus.jsonl \
  --audit artifacts/corpus_audit.json

python scripts/shard_corpus.py \
  --input artifacts/corpus.jsonl \
  --output-dir artifacts/shards \
  --records-per-shard 10000
```

The pipeline refuses a source whose license is `unknown` or which is not approved for training.

## 2. Train the tokenizer

```bash
om-ai tokenizer train \
  --input artifacts/corpus.jsonl \
  --output artifacts/tokenizer.json \
  --vocab-size 32000
```

For a real large model, train the tokenizer on a representative sample of the final multilingual/code corpus before pretraining.

## 3. Pretrain model weights

Development run:

```bash
om-ai train \
  --config configs/tiny.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --steps 1000
```

Multi-GPU DDP:

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --config configs/1b.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer.json
```

Multi-GPU FSDP:

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --strategy fsdp \
  --config configs/7b.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer.json
```

DeepSpeed ZeRO-3:

```bash
deepSpeed --num_gpus 8 -m om_ai.training.deepspeed_train \
  --config configs/7b.json \
  --data artifacts/corpus.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --deepspeed configs/deepspeed_zero3.json
```

For multi-node execution, use the cluster launcher for your environment and provide rank/world-size/master address variables required by torch.distributed or DeepSpeed.

## 4. Supervised instruction tuning (SFT)

Training format:

```json
{"system":"optional system instruction","prompt":"user request","response":"preferred assistant answer"}
```

Run:

```bash
om-ai sft \
  --config configs/7b.json \
  --data /data/om_instruction_data.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/checkpoints/latest.pt \
  --steps 10000 \
  --batch-size 2 \
  --lr 2e-5
```

The SFT trainer masks the prompt tokens and optimizes only the assistant response tokens.

## 5. Preference data and reward model

Preference format:

```json
{"prompt":"question","chosen":"better answer","rejected":"worse answer"}
```

Train the pairwise reward model:

```bash
om-ai reward \
  --config configs/7b.json \
  --data /data/om_preferences.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/sft/latest.pt \
  --steps 5000
```

The included reward trainer optimizes a Bradley-Terry/log-sigmoid pairwise preference objective.

## 6. Direct Preference Optimization (DPO)

```bash
om-ai dpo \
  --config configs/7b.json \
  --data /data/om_preferences.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/sft/latest.pt \
  --steps 5000 \
  --beta 0.1
```

DPO uses a frozen reference copy of the starting policy and optimizes the preferred response over the rejected response without requiring an online reward-model rollout loop.

## 7. Benchmark and regression reports

```bash
om-ai benchmark \
  --config configs/7b.json \
  --tokenizer artifacts/tokenizer.json \
  --checkpoint artifacts/dpo/latest.pt \
  --benchmark benchmarks/core.jsonl \
  --report artifacts/eval/report.json
```

Extend the benchmark JSONL with licensed/internal evaluation sets for language, reasoning, code, math, safety, tool-use, domain knowledge and regression tests.

## 8. Feedback -> continuous post-training data

Store explicit user feedback:

```bash
om-ai feedback add \
  --prompt "original prompt" \
  --response "model answer" \
  --rating 2 \
  --preferred-response "corrected answer"
```

Export it as SFT and preference data:

```bash
om-ai feedback export
```

Never train directly on raw production conversations without an explicit privacy, consent, retention, redaction and licensing policy.

## 9. Vision and voice

`om_ai.vision.VisionTransformerEncoder` is a trainable ViT-style image encoder. `MultimodalProjector` maps image tokens into the OM decoder dimension and `OMVisionLanguageModel` sends them through decoder cross-attention.

`om_ai.voice.AudioFeatureExtractor`, `SpeechEncoder` and `CTCASRModel` provide a trainable local speech-recognition foundation. They still require large paired image/text and speech/text datasets to become useful production models.

## 10. What creates actual intelligence

The source code defines the learning system. The intelligence in a neural model is materially encoded in the trained weights. Therefore the actual production sequence is:

`licensed corpus -> tokenizer -> pretraining -> checkpoints -> instruction data -> SFT -> preference data -> reward/DPO -> evaluations -> red-team fixes -> deployment -> feedback -> controlled retraining`

The repository can execute every software stage above. It cannot create frontier-scale learned weights without actually supplying the corpus and compute and running those optimization steps.
