# OM Chat: dynamic cloud-model setup

OM's chat API can use either the native OM checkpoint or a server-side OpenAI-compatible cloud model. Memory, RAG, agent, and intelligence flags do not by themselves make a small local checkpoint equivalent to a frontier cloud model.

## Enable cloud-backed replies for `POST /v1/chat`

1. Keep your existing repository-root `.env`; do **not** replace it with `.env.example`.
2. Set these values in `.env`:

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

   For another OpenAI-compatible cloud provider, use its documented base URL and exact model ID. Do not guess the endpoint or model name.

3. Restart the API after editing `.env`.
4. Test multiple turns against `POST /v1/chat` and confirm the response reports the configured cloud provider/model. Keep the provider key on the server. Never place it in React/Vite `VITE_*` variables or commit it to Git.

## Why explicit selection matters

Older configuration may contain `OM_MODEL_PROVIDER=om_native`. The backend now honors an explicit `OM_AI_CHAT_BACKEND=openai` selection before that stale provider setting. Set both variables to `openai` for an unambiguous configuration.

## Boundaries and gotchas

- This changes the backend for `POST /v1/chat`; it does not silently switch every unrelated model endpoint, retrain OM weights, or make the local OM checkpoint equal to a frontier model.
- A cloud account, valid API key, model access, and network connectivity are required. Without these, cloud replies cannot work.
- Keep native checkpoint settings if other endpoints still need the local model.
- Remove duplicate definitions of `OM_CHAT_MAX_NEW_TOKENS`. Dotenv parsers commonly use the last occurrence, which can override a larger value with a smaller one.
- Revoke and replace any key pasted into chat, source control, logs, or a browser bundle before testing.
