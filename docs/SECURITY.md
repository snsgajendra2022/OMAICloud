# Security Baseline

OM AI tools can affect real systems, so tool execution must be treated as privileged infrastructure.

## Implemented in `om_ai/security/`

| Module | Capability |
|--------|------------|
| `auth.py` | API key authentication, `TenantContext`, role-based access (`RBAC`: admin / operator / agent / viewer) |
| `accounts.py` | Email/password accounts + session tokens (SQLite `OM_AI_ACCOUNTS_DB`) |
| `tokens.py` | Named machine API tokens (SQLite `OM_AI_TOKENS_DB`) |
| `ssrf.py` | `SSRFGuard` for outbound URL fetches (OpenAPI discovery, connectors) |
| `audit.py` | `AuditLog` — persistent audit entries |
| `rate_limit.py` | `RateLimiter` / `RateLimitExceeded` (API uses `OM_AI_RATE_LIMIT`) |
| `secrets.py` | `SecretStore` — keep credentials out of prompts and logs |

Wired into FastAPI via `om_ai/api/deps.py` and `om_ai/api/main.py` (`require_auth`, `require_permission`).

### Account API (`/v1/auth/*`)

- `POST /v1/auth/register` — create user (disable with `OM_AI_ALLOW_REGISTER=0`)
- `POST /v1/auth/login` — issue session Bearer token
- `POST /v1/auth/logout` — revoke current session
- `POST /v1/auth/logout-all` — revoke all sessions for the user
- `GET /v1/auth/me` — current identity
- Passwords: scrypt; sessions: hashed secrets in `artifacts/accounts.sqlite3`
- Auth endpoints have an extra per-IP rate limit (`OM_AI_AUTH_RATE_LIMIT`)

## Production requirements

- authentication and tenant-scoped authorization
- deny-by-default tool permissions (`SafeShellTool` allowlists; `OM_AI_ALLOWED_SHELL`)
- isolated worker processes/containers
- secret manager; never place API keys in prompts or logs
- outbound network egress controls + SSRF guards on URL tools
- command and filesystem allowlists
- approval gates for destructive/high-impact agent tools
- immutable audit logs
- per-tenant encryption keys where required
- request limits, quotas and abuse monitoring
- signed model/checkpoint artifacts (`om_ai/checkpoint/`)
- supply-chain scanning and pinned dependencies

Never expose the API to the public internet without TLS, auth, rate limits, and hardened tool permissions.
