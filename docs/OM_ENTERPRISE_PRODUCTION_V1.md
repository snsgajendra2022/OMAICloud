# OM AI Enterprise Production Architecture v1.0

**Code, not slides.** Build with:

```bash
om-ai platform build
om-ai platform health
om-ai platform workflow --request "Create React login page"
om-ai platform route --path chat --prompt "Create React login page"
om-ai platform route --path metrics
```

## Services (13 healthy)

identity · users · billing · audit · model_gateway · model_lifecycle · agents · reasoning · knowledge · retrieval · memory · evaluation · learning

## Layout

- `services/` — full microservice mesh (in-process locally)
- `ai_platform/` — orchestration, policies, prompts, workflows, agent capability.json
- `data_platform/` · `training_platform/` · `infrastructure/{docker,kubernetes,monitoring,terraform}`
- `security/` — authentication/encryption/secrets/compliance facades

## Report

`artifacts/ENTERPRISE_PLATFORM_REPORT.json`

## Honest boundary

In-process service mesh for Mac. Split deploy via Docker/K8s. GPU weights + managed Postgres/Vector remain external.
