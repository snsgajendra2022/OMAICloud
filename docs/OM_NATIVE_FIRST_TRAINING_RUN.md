# OM-1.1 Native Training: First Safe Run

## Goal

Validate the first larger native OM architecture without replacing the current OM-1.0 checkpoint or registry. The 300M preset is an architecture only; it is randomly initialized until trained.

## Architecture presets

- `configs/om-1.1-300m.json`: estimated about 285.2M parameters with the current `ModelConfig.parameter_estimate()`.
- `configs/om-1.1-1b.json`: estimated about 1.248B parameters with the current estimator.
- Neither preset is a trained model or evidence of improved capability.

## 1. Validate the config before allocating model memory

From the repository root with the project's virtual environment active:

```bash
python -m om_ai.cli model-info --config configs/om-1.1-300m.json
python -m om_ai.cli model-info --config configs/om-1.1-1b.json
python -c "import torch; print('PyTorch:', torch.__version__); print('MPS built:', torch.backends.mps.is_built()); print('MPS available:', torch.backends.mps.is_available())"
pytest -q tests/test_native_model_architecture_presets.py
```

The expected parameter estimates are approximately 285,245,440 and 1,247,903,744 respectively. Small differences may occur if the parameter estimator is deliberately updated to reflect model implementation details.

## 2. Do not use the OM-1.0-specific training wrapper for a new model

The legacy `train-om1` path syncs OM-1.0 registry metadata. Do not use it to train the 300M or 1B preset until that wrapper has a model-id-aware registry path. Use the generic `pretrain` command for an isolated experiment output directory.

First prepare a small, explicitly licensed text file for a pipeline smoke test, or point `--data` at an existing prepared corpus. Do not treat synthetic smoke-test text as useful pretraining data.

Example smoke command (this is a pipeline check, not meaningful pretraining):

```bash
om-ai pretrain \
  --config configs/om-1.1-300m.json \
  --tokenizer artifacts/tokenizer-production-65536.json \
  --data /path/to/your/prepared-smoke-corpus.txt \
  --steps 2 \
  --batch-size 1 \
  --grad-accum 1 \
  --precision fp32 \
  --device mps \
  --output artifacts/checkpoints/om-1.1-300m-smoke \
  --checkpoint-every 1 \
  --log-every 1
```

Replace the corpus path with a real local file. If the tokenizer file does not exist, stop and locate the repository's verified tokenizer; never pair a checkpoint with an unverified tokenizer.

## 3. Before a real pretraining run

- Verify corpus licenses, language/domain mix, deduplication, and held-out validation split.
- Record the tokenizer fingerprint and corpus manifest.
- Measure throughput and peak memory with the smoke run.
- Confirm checkpoint save and resume work.
- Start with a short pilot; estimate full training duration from measured tokens/second.
- Keep all candidate artifacts under `om-1.1-300m` paths. Do not change the default native OM model or production registry until evaluation gates pass.

## Honest status

Passing config tests or completing a smoke run proves only that the pipeline executes. It does not prove language quality, broad reasoning, production readiness, or GPT-5 parity. Promote a candidate only after held-out evaluation shows a repeatable improvement over the frozen OM baseline.
