# OM Native Chat Diagnostics

Use this when the chat UI reports that the native checkpoint did not produce a usable model-generated answer. This diagnostic uses **OM's local checkpoint only** and does not call a hosted LLM provider.

## 1. Update the branch

```bash
git checkout feature/gpt5-production-runtime
git pull origin feature/gpt5-production-runtime
```

## 2. Check local model assets

The `artifacts/` directory is intentionally git-ignored. Pulling the repository does not download your trained checkpoint or tokenizer. The three configured files must exist on the machine running OM:

- `OM_MODEL_CONFIG`: architecture configuration used for that checkpoint
- `OM_MODEL_TOKENIZER`: tokenizer trained/bound with those weights
- `OM_MODEL_CHECKPOINT`: actual trained `.pt` checkpoint

Relative paths in these variables are resolved from the repository root, even if the server was launched from another working directory. Do not use `tokenizer-fixed-v3.json` with a checkpoint whose embedding vocabulary is 65536.

## 3. Run a real native inference check

From the repository root, activate the same virtual environment used by the server. If your local `.env` is shell-compatible, load it and run:

```bash
set -a
source .env
set +a
python scripts/diagnose_native_chat.py
```

The script prints the resolved paths, checkpoint size, load outcome, tokenizer fingerprint, device, and three short generated answers. It returns exit code 2 when loading fails and 3 when generation is empty or unusable.

Do not paste secrets from your `.env` into issues or chat. The diagnostic does not print API keys.

## 4. Interpret the result

- **Checkpoint missing:** put the intended trained checkpoint at the configured path or correct `OM_MODEL_CHECKPOINT`.
- **Tokenizer vocabulary mismatch:** use the tokenizer from the same training run. The embedding vocabulary and tokenizer vocabulary must match.
- **Tokenizer fingerprint mismatch:** use the tokenizer bound to that checkpoint, or intentionally re-bind only after verifying it is the correct tokenizer for those weights.
- **Incompatible checkpoint / missing critical tensors:** the model architecture and checkpoint do not match. Use the matching config and checkpoint; OM now rejects substantially partial loads instead of silently generating from random-initialized parameters.
- **Loads but all three generations fail:** inspect the full local server traceback and the checkpoint's training/evaluation history. A successful file load proves compatibility, not that the weights are sufficiently trained for useful conversation.

## 5. Feature capability reality

OM Pulse, ChatOM Mind, ReasonOM Forge, AgentOM Nova, CreateOM Matrix, and Orchestrate should be treated as capabilities/modes coordinated around the native OM model—not six independent trained LLMs unless separate compatible checkpoints, routing, and evaluations actually exist. Retrieval, tools, memory, and orchestration can improve grounding and task execution, but they cannot manufacture missing language-model capability. Reaching frontier-assistant quality requires appropriately licensed training data, substantial training compute, instruction/alignment training, and regression evaluation.

## 6. Server check

Restart the server after changing `.env`. Then verify the runtime model status and run several different prompts, including a follow-up that refers to the previous turn. Keep the native provider selected:

```bash
OM_MODEL_PROVIDER=om_native
OM_AI_CHAT_BACKEND=om_native
OM_NATIVE_MODEL_FIRST=1
```

Never add a hosted-provider fallback merely to hide a native generation failure.
