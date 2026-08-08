# Deployment

## Local process

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
om-ai serve --host 0.0.0.0 --port 8080
```

## Docker

```bash
docker compose up --build
```

- `Dockerfile`: Python 3.12-slim, installs package, `CMD om-ai serve`
- `docker-compose.yml`: port 8080, mounts `./artifacts` → `/data`, sets `OM_AI_DB` / `OM_AI_REGISTRY`

## Environment (see `.env.example`)

Typical vars: `OM_AI_DB`, `OM_AI_KB`, `OM_AI_AUDIT_DB`, `OM_AI_REGISTRY`, `OM_AI_RATE_LIMIT`, `OM_AI_ALLOWED_SHELL`, `OM_AI_CORS_ORIGINS`, API key configuration used by `om_ai/security/auth.py`.

## Production checklist

- TLS terminator / reverse proxy
- Auth enabled; no open CORS to `*`
- Network egress controls for tools
- Rate limits + audit DB backups
- Signed/integrity-checked model bundles (`om_ai/checkpoint/`)
- Do not publish GPU training containers with secrets baked in

## Scope

This package deploys the **platform**. Large models need separate weight storage, GPU nodes, and a registry promotion process (`MODEL_REGISTRY.md`).
