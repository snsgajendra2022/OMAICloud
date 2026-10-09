# OM Chat: dynamic cloud-model setup

OM's chat API can use either the native OM checkpoint or a server-side OpenAI-compatible cloud model. The model backend must actually be configured; memory/RAG/agent feature flags do not turn a small local checkpoint into a frontier cloud model.

## Enable cloud-backed replies for `POST /v1/chat`

1. Keep your existing `.env` file. Do **not** replace it with `.env.example`.
2. Set these values in the repository-root `.env`:

   ```dotenv
   OM_AI_CHAT_BACKEND=openai
   OM_MODEL_PROVIDER=openai
   OM_AI_OPENAI_BASE_URL=https://api.openai.com/v1
   OM_AI_OPENAI_MODEL=gpt-4o-mini
   OM_AI_OPENAI_API_KEY=replace-with-a-new-provider-key
   OM_CHAT_MAX_NEW_TOKENS=512
   OM_CHAT_TEMPERATURE=0.7
   OM_CHAT_TOP_P=0.9
   ```

   If your cloud vendor provides an OpenAI-compatible API, use its documented base URL and model ID instead. This repository cannot infer a vendor endpoint or model name.

3. Restart the API process after changing `.env`.
4. Verify `GET /api/v1/model` / server logs and send multiple turns to `POST /v1/chat`. The API response should report the configured cloud provider/model. Never expose the provider key in React/Vite environment variables or commit it to Git.

## Why explicit selection matters

Older configuration can contain `OM_MODEL_PROVIDER=om_native`. The chat backend now honors an explicit `OM_AI_CHAT_BACKEND=openai` selection before that stale provider setting. Setting both variables to `openai` makes the intended mode unambiguous.

## Important boundaries

- This changes the backend used by `POST /v1/chat`; it does not replace the model for every unrelated endpoint, retrain OM weights, or make OM's local checkpoint equal to a frontier model.
- A cloud provider account, valid API key, model access, and network connectivity are required. The repository cannot make cloud calls without them.
- Keep your OM native checkpoint settings if other endpoints still need the local model.
- Remove duplicate definitions of `OM_CHAT_MAX_NEW_TOKENS`; dotenv parsers commonly use the last occurrence, which can silently override a larger value with a smaller one.
- Revoke any key that has been pasted into chat, source control, logs, or a browser bundle and replace it before testing.
