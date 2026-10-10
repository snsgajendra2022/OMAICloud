# Pretrained model runtime and 70B deployment

## Two separate model paths

OM's custom native model remains available through OM_MODEL_PROVIDER=om_native. It uses OM checkpoints and OM's tokenizer. The optional Transformers provider is a different path for a compatible pretrained causal language model and uses that model's tokenizer and chat template. A missing Transformers model never triggers an implicit provider fallback.

This code provides runtime support, not pretrained weights. It does not claim that the checked-in OM-1.0 checkpoint is a 70B model or that 70B training has occurred.

## Install

    pip install -e '.[hf]'
    # For supported CUDA/Linux 4-bit or 8-bit inference:
    pip install -e '.[hf-quant]'

Quantization support varies by OS, CUDA, GPU, driver, PyTorch, and bitsandbytes versions. The optional quantization extra deliberately does not promise Mac/MPS compatibility.

## Configure

Set these in your local ignored .env or process environment. Do not commit credentials or private model tokens.

    OM_MODEL_PROVIDER=om_native
    OM_HF_MODEL=
    OM_HF_DEVICE_MAP=auto
    OM_HF_DTYPE=auto
    OM_HF_QUANTIZATION=none
    OM_HF_TRUST_REMOTE_CODE=false
    # Optional JSON string, e.g. {"0":"40GiB","1":"40GiB","cpu":"96GiB"}
    OM_HF_MAX_MEMORY=

Use OM_HF_MODEL for a local model directory or a Hugging Face model ID whose license and access terms you have reviewed. Set OM_HF_TRUST_REMOTE_CODE=true only after reviewing the repository code. Gated repositories may require a separately configured Hugging Face login/token; never paste the token into source code.

The adapter can be initialized from Python:

    from om_ai.backends.transformers_backend import TransformersBackend

    backend = TransformersBackend()
    info = backend.load(
        model_id="path/to/your/local/model",
        device_map="auto",
        quantization="4bit",
        local_files_only=True,
    )
    print(info)  # includes actual loaded parameter count
    print(backend.chat([{"role": "user", "content": "Hello"}]))

The example model path is a placeholder, not an included model. A tokenizer chat template is required; the adapter refuses to invent a generic template if one is absent. For chat templates with special role constraints, validate the selected model's supported message schema.

## Verify the actual model

The adapter counts loaded model parameters and reports model ID, model type, quantization, device map, and template availability. Parameter count alone does not prove quality, licensing, or complete hardware residency. Review the model configuration, weight shards, license, model card, tokenizer, and evaluation results.

For an initial memory estimate:

    python scripts/estimate_llm_memory.py --parameters 70000000000 --precision int4 --context 8192 --concurrency 1
    python scripts/estimate_llm_memory.py --parameters 70000000000 --precision fp16 --context 4096 --output artifacts/evaluations/70b-memory-estimate.json

The estimate includes a configurable KV-cache approximation and runtime overhead, but it is not a substitute for a measured load test. Update layers, KV heads, head dimension, precision, context, and concurrency to match the chosen model. Inference is much cheaper than full pretraining; training 70B from scratch requires a substantial distributed GPU cluster, data, storage, and training operations.

## Dataset manifest validation

Before running SFT, validate a source dataset without printing its records:

    python scripts/validate_chat_dataset.py data/example_sft.jsonl --output artifacts/manifests/example-sft-validation.json
    python scripts/validate_chat_dataset.py data/train.jsonl --eval-dataset data/eval.jsonl --output artifacts/manifests/train-validation.json

Accepted records are chat messages or prompt/completion JSON objects. Parquet is supported when pandas and a Parquet engine are installed. The validator reports a source SHA-256, malformed rows, exact duplicates, and exact overlap with the evaluation dataset. It does not verify licenses, semantic duplicates, or model quality; those require separate review.

## Known limits

- This adapter is an explicit runtime building block; it is not a claim that the existing application API already exposes every provider feature.
- Streaming uses Transformers' TextIteratorStreamer. Consumer disconnect does not reliably cancel an in-flight GPU kernel; production request cancellation needs a serving engine with supported cancellation semantics.
- device_map=auto is best-effort placement, not a guarantee that a model fits. A load can fail if memory is insufficient.
- The optional 4-bit/8-bit bitsandbytes path is targeted at supported environments, especially CUDA/Linux. Validate actual hardware before choosing it.
- No large weights or datasets are added to Git. Store them using approved artifact storage or Git LFS only if the repository's storage budget and policy permit.
- A production 70B service still needs authentication, request limits, isolation, telemetry, load testing, and deployment validation around the inference endpoint.
