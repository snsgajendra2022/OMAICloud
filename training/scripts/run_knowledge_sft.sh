#!/usr/bin/env bash
set -euo pipefail
om-ai sft \
  --config configs/omai-20m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --checkpoint artifacts/checkpoints/omai-20m-base/latest.pt \
  --data data/om-knowledge-brain-v1/train/om_knowledge_instruct_v1.jsonl \
  --output artifacts/checkpoints/om-1.0-knowledge-sft \
  --steps 500 --device mps --checkpoint-every 250
