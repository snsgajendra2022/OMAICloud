# Integrations

Package: `om_ai/integrations/`.

| Module | Role |
|--------|------|
| `plugin.py` | `IntegrationPlugin` ABC, `ActionSpec`, `PluginRegistry` |
| `http_connector.py` | Restricted REST connector (SSRF-aware usage patterns) |
| `whatsapp.py` | WhatsApp transport **contract** + development adapter |

Discovery helpers: `om_ai/discovery/openapi.py` (OpenAPI tool), `om_ai/discovery/project.py` (`om-ai project-scan`).

## Plugin pattern

Implement `health()`, `actions()`, `execute(action, arguments)`; register with `PluginRegistry`. Keep secrets in `om_ai/security/secrets.py` / env — never in prompts.

## What you must supply

Product schemas, credentials, compliance review, and tests for each CRM/ERP/channel. Generic connectors do not magically understand every SaaS API.

## WhatsApp

Production session/transport credentials and platform-policy compliance are **external**. The repo ships an adapter interface suitable for local/dev wiring, not a claimed production Meta Business deployment.
