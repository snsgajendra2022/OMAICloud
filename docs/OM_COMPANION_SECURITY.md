# OM Companion Security

## Principles

- Least privilege
- Structured `ActionRequest` only (no model→shell string)
- `subprocess(..., shell=False)`
- External document content cannot grant permissions
- Destructive / sensitive actions require explicit approval
- Secrets redacted from logs
- Filesystem bounded by sandbox roots
- Ambient mic audio not stored by default

## Approval

Say **yes** / **no** during a pending permission, or use:

- `POST /api/companion/permissions/{id}/approve`
- `POST /api/companion/permissions/{id}/deny`

Audit: `artifacts/companion/actions_audit.jsonl`
