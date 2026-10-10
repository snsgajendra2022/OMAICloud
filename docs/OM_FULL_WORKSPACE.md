# OM Full Workspace — Native-Only Startup

This branch adds a repeatable startup path for the existing OM AI workspace. It keeps the current chat UI, companion UI, APIs, memory, retrieval, tools, and native runtime in the same application; it does not create a separate demo or silently route prompts to a hosted LLM.

## Start the app on macOS or Linux

From the repository root:

```bash
bash scripts/start_om_workspace.sh
```

Then open:

- Chat workspace: http://127.0.0.1:8080/chat
- Companion UI: http://127.0.0.1:8080/companion
- API documentation: http://127.0.0.1:8080/docs

The script checks Python 3.11+, creates `.venv` when absent, installs the project dependencies when needed, enforces the native OM provider for that server process, and starts the API. Use `Ctrl+C` to stop the server.

Optional host/port overrides:

```bash
OM_HOST=0.0.0.0 OM_PORT=8080 bash scripts/start_om_workspace.sh
```

Do not expose a development server publicly without authentication, TLS, rate limits, and a reviewed network policy.

## Verify native generation

In a second terminal, from the same repository and virtual environment:

```bash
source .venv/bin/activate
python scripts/diagnose_native_chat.py
pytest -q
```

The diagnostic must load the real checkpoint and produce usable output for all prompts. A missing checkpoint does not stop the UI from starting, but it does mean the app cannot provide reliable model-generated answers. The configured tokenizer must belong to the same trained model run and match its vocabulary.

## What “100% cloud AI parity” means for this project

Treat parity as an evaluation target, not a setting. Evaluate OM against a named reference model on the same held-out prompts across conversation, instruction following, coding, reasoning, math, context retention, retrieval/tool use, multimodal tasks (when implemented), latency, and reliability. Keep per-category scores and error examples. Do not publish a 100% claim unless the measured results support it.

A UI, memory store, RAG, agents, or more Python code cannot substitute for missing learned capabilities in the model weights. Frontier-level quality requires suitable licensed training data, substantial training compute, post-training/alignment, and repeated evaluations. The runtime remains native-only; it should report a model failure clearly rather than hiding it with a hosted fallback.
