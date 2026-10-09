# Native OM dynamic chat

This change keeps OM chat on the **native OM checkpoint**. It does not call OpenAI, Cloud AI, Ollama, or another external text-generation provider.

## What the change fixes

The existing chat path had several deterministic shortcuts that could return the same greeting/identity text without letting the native checkpoint generate a response:

- intent enrichment could return a direct reply;
- the ChatGPT-style runtime could return before the main model-generation path;
- the chat pipeline could return a canned greeting/thanks response before generation;
- long pre-written drafts could suppress native model generation.

With `OM_NATIVE_MODEL_FIRST=1` (the default), these shortcuts are bypassed for the chat hot path. The native model is asked to synthesize the final answer from the user turn, conversation history, and available internal context. Memory, retrieval, tools, and reasoning may provide context, but should not be mistaken for the language model itself.

## Keep the native provider

In the repository-root `.env`, keep:

```dotenv
OM_MODEL_PROVIDER=om_native
OM_AI_CHAT_BACKEND=om_native
OM_NATIVE_MODEL_FIRST=1
OM_CHAT_PIPELINE=1
OM_CHAT_MEMORY=1
OM_CHAT_RAG=1
OM_CHAT_FILE_RAG=1
OM_UNDERSTANDING=1
OM_COGNITIVE_INTELLIGENCE=1
OM_UNIVERSAL_INTELLIGENCE=1
OM_STATIC_TEMPLATES=0
```

Do not add cloud API keys or switch the provider to `openai`. Preserve your existing database, auth, audit, memory, upload, and registry settings.

## Important configuration cleanup

Your provided environment contains duplicate generation variables. Keep only one active definition each for `OM_CHAT_TEMPERATURE`, `OM_CHAT_TOP_P`, `OM_CHAT_TOP_K`, `OM_CHAT_REPETITION_PENALTY`, and `OM_CHAT_MAX_NEW_TOKENS`. The later duplicate may override the earlier one. For longer answers, use a value such as `OM_CHAT_MAX_NEW_TOKENS=512`, provided the model's context window and available memory support it.

Restart the API after changing `.env`. Run:

```bash
pytest -q tests/test_native_model_first.py tests/test_chat_backend.py
om-ai model-info
om-ai serve --host 127.0.0.1 --port 8080
```

In another terminal, send several different messages and follow-ups to `POST /v1/chat`; inspect the response metadata and server logs to confirm the native backend is loaded and the model-generation stage is used.

## What this cannot do by itself

This removes shortcut replies; it does **not** magically make the current checkpoint equal to a frontier cloud model. OM's own intelligence depends on the actual checkpoint weights, tokenizer compatibility, training corpus, SFT/DPO quality, context length, inference implementation, and evaluation. If the current checkpoint is tiny, undertrained, missing, or incompatible, OM can still answer poorly. The next required work is to run the actual model, evaluate representative tasks, fix checkpoint/tokenizer/context issues, and train/align on licensed data with sufficient compute. This patch does not claim that all modules/files have been individually upgraded or that cloud-level parity has been achieved.
