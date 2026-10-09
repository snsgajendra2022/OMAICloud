# OM Chat — React workspace

This is a React/Vite client for the existing OM AI FastAPI chat endpoint. It does not ship a mock model or hard-coded assistant answers: each submitted turn is sent to `POST /v1/chat`, which routes through the repository's configured chat backend and existing intelligence pipeline.

## Run locally

1. Start the OM AI API from the repository root:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev,companion]'
   cp .env.example .env  # if you have not configured the environment yet
   om-ai model-info
   om-ai serve --host 127.0.0.1 --port 8080
   ```

   Confirm that your `.env` points to an existing, compatible checkpoint and tokenizer. Native OM is the default; this UI does not bypass or silently replace it with another provider.

2. In another terminal:

   ```bash
   cd web/om-chat
   cp .env.example .env
   npm install
   npm run dev
   ```

3. Open the Vite URL printed in the terminal (normally `http://localhost:5173`).

## Configuration

- `VITE_OM_API_URL`: API origin, default `http://127.0.0.1:8080`.
- `VITE_OM_API_KEY`: optional bearer token only if your API's auth configuration expects it. Never place privileged production keys in a public browser build.

If Vite runs on a different origin, set `OM_AI_CORS_ORIGINS=http://localhost:5173` in the server environment and restart the API. The endpoint requires the server's `model.generate` permission. The client stores the latest 80 user/assistant messages in this browser's local storage; use **New conversation** to clear them.

## Verify

```bash
npm run build
```

Then send a message and verify the API response includes `reply`, `provider`, and `model`. A missing checkpoint or permission error should be surfaced instead of being replaced with a fabricated answer.
