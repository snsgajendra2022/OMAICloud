# Self-hosted LLM runtime (GPT-5-level target)

## Goal and honest boundary

OM AI is the product/platform: chat API, user experience, conversations, retrieval, memory, tools, safety, observability, and evaluations. A capable open-weight language model is the primary generation engine, served separately by vLLM. The small OM-1.0 native checkpoint is not the production brain in this configuration.

This architecture targets high-end assistant capability; it does **not** make OM AI GPT-5, provide GPT-5 weights, or guarantee GPT-5 parity. Capability depends on the selected model, its license, hardware, inference settings, tool integration, data quality, and measured benchmark results. The platform layer cannot manufacture frontier model intelligence by itself.

## Runtime topology

- OM API: existing FastAPI service, selected with `OM_MODEL_PROVIDER=vllm`.
- Inference: vLLM OpenAI-compatible `/v1/chat/completions` endpoint.
- Model weights: downloaded by vLLM from the configured licensed model repository, or mounted from a local model directory.
- Context and tools: OM AI owns conversation preparation, retrieval, memory, auth, and application-level tool permissions.
- Failure policy: a missing model ID, unavailable server, or malformed response is an explicit error. There is no silent downgrade to the small native checkpoint.

The adapter uses the standard OpenAI-compatible chat API documented by vLLM: https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/. The model must support a compatible chat template. Template behavior is model-specific: https://huggingface.co/docs/transformers/chat_templating.

## Configure the model

1. Choose a model after checking its license, supported context length, tool-call behavior, language coverage, benchmark evidence, and memory requirements.
2. Put the exact served model ID in `OM_VLLM_MODEL`. Do not assume a 70B or mixture-of-experts model fits your server; use `scripts/estimate_llm_memory.py` for an initial rough estimate and then measure actual GPU memory.
3. Configure `OM_VLLM_BASE_URL` for the OM API. When using the supplied Compose override, it is `http://vllm:8000/v1` inside the Compose network.
4. Keep the vLLM endpoint on a private network. Add a gateway, TLS, authentication, and rate limiting before exposing any endpoint outside a trusted network.
5. Start and validate the model server before sending production traffic.

### Compose on a Linux host with NVIDIA Container Toolkit

Copy `.env.example` to `.env`, set `OM_VLLM_MODEL` to the exact chosen model ID, and set a private deployment secret for `OM_VLLM_API_KEY`. Then run:

```bash
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up --build
```

The vLLM service requires a compatible NVIDIA GPU, NVIDIA Container Toolkit, and enough aggregate GPU memory for the selected model and its KV cache. The Compose override intentionally does not publish the inference port to the host; the API reaches it over the internal Compose network. For CPU/Mac development, run a compatible local inference server and point `OM_VLLM_BASE_URL` at it, or use the optional Transformers provider for smaller models.

## Runtime configuration

```dotenv
OM_MODEL_PROVIDER=vllm
OM_AI_CHAT_BACKEND=vllm
OM_VLLM_BASE_URL=http://127.0.0.1:8000/v1
OM_VLLM_MODEL=your-exact-served-model-id
OM_VLLM_API_KEY=your-private-server-key
```

When OM API and vLLM are in separate Compose services, use `http://vllm:8000/v1` instead of localhost. The model name must exactly match the name vLLM serves.

## Acceptance checklist

- [ ] Verify the chosen model license and allowed commercial use.
- [ ] Confirm server health and exact served model ID.
- [ ] Verify the OM chat endpoint returns a model-generated answer.
- [ ] Verify no native fallback occurs when vLLM is stopped or misconfigured.
- [ ] Test long-context behavior, multi-turn memory, retrieval citations, and tool permissions.
- [ ] Run a fixed evaluation set against OM AI and a chosen reference model using identical prompts and scoring.
- [ ] Measure tokens/sec, time-to-first-token, p50/p95 latency, peak GPU memory, concurrency, and failure recovery.
- [ ] Run auth, tenant isolation, prompt-injection, SSRF, rate-limit, and secret-leakage tests.
- [ ] Only label the release production-ready after all required gates pass.

## What this does not complete automatically

This integration does not provide model weights, GPU servers, paid compute, a licensed training corpus, training runs, or benchmark proof. Training a frontier-scale model from scratch requires a separate, very large compute/data program. A realistic path is to start from a capable licensed model, establish baseline metrics, improve OM's tool/RAG/product layers, then fine-tune on lawful high-quality data and re-evaluate.
