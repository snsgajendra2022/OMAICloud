# Distributed Training

Entry points live under `om_ai/training/`. Use a Linux + CUDA cluster for anything beyond tiny/smoke runs.

## DDP (default)

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --strategy ddp \
  --config configs/1b.json \
  --data /data/train.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --steps 1000 \
  --batch-size 1 \
  --output artifacts/checkpoints
```

Module: `om_ai/training/distributed.py` — `DistributedDataParallel`, `DistributedSampler`, NCCL (CUDA) or gloo (CPU).

## FSDP

```bash
torchrun --standalone --nproc_per_node=8 -m om_ai.training.distributed \
  --strategy fsdp \
  --config configs/7b.json \
  --data /data/train.jsonl \
  --tokenizer artifacts/tokenizer.json
```

Wraps `OMTransformer` in PyTorch `FullyShardedDataParallel`. Prefer FSDP or DeepSpeed when a replica no longer fits on one GPU.

## DeepSpeed ZeRO-3

```bash
pip install -e '.[deepspeed]'
deepspeed --num_gpus 8 -m om_ai.training.deepspeed_train \
  --config configs/7b.json \
  --data /data/train.jsonl \
  --tokenizer artifacts/tokenizer.json \
  --deepspeed configs/deepspeed_zero3.json
```

Module: `om_ai/training/deepspeed_train.py`. Config: `configs/deepspeed_zero3.json`.

## Multi-node

Set the usual torch.distributed / DeepSpeed env vars (`MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK`, …) via your scheduler (Slurm, K8s, etc.). The repo provides the training entry points; cluster orchestration is environment-specific.

## Practical notes

- Enable `gradient_checkpointing` in larger configs (`7b`/`13b`/`70b` presets already set it true where appropriate).
- Rank 0 writes checkpoints; verify with `om-ai bundle` / registry before promotion.
- Distributed scripts are real launch paths, not magic — wall-clock time and token budget still determine quality.
