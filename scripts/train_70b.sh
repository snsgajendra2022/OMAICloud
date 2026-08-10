#!/usr/bin/env bash
set -euo pipefail

: "${OM_AI_70B_DATA:?Set OM_AI_70B_DATA=/path/to/licensed/corpus}"
: "${OM_AI_70B_TOKENIZER:?Set OM_AI_70B_TOKENIZER=/path/to/production/tokenizer.json}"

OM_AI_70B_CONFIG="${OM_AI_70B_CONFIG:-configs/70b.json}"
OM_AI_70B_OUTPUT="${OM_AI_70B_OUTPUT:-artifacts/checkpoints/om-70b}"
OM_AI_70B_DEEPSPEED="${OM_AI_70B_DEEPSPEED:-configs/deepspeed_zero3.json}"

python3 scripts/om70b_preflight.py \
  --config "$OM_AI_70B_CONFIG" \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER"

exec deepspeed om_ai/training/deepspeed_train.py \
  --config "$OM_AI_70B_CONFIG" \
  --data "$OM_AI_70B_DATA" \
  --tokenizer "$OM_AI_70B_TOKENIZER" \
  --deepspeed "$OM_AI_70B_DEEPSPEED"
