# Independent API contract

Base path: `/api/v1`. Version0.1.0 OpenAPI schema is served at `/api/v1/openapi.json`; interactive documentation at `/api/v1/docs`. This is an independent service boundary for future Guardrail Sovereign integration. No Guardrail Sovereign database or internal API is used.

Authenticate with `POST /auth/login` using `{email,password}`. Store the returned opaque bearer token securely. Each tenant endpoint requires `Authorization: Bearer <token>` and `X-Tenant-ID: <membership tenant_id>`. `/auth/me` lists available memberships. `/auth/logout` revokes the current token. Sessions expire after SESSION_HOURS (default8). Use a dedicated tenant member identity for an API consumer; scoped long-lived service tokens/OIDC are future work.

| Module | Endpoint families |
|---|---|
| Inventory/discovery | `/systems`, `/bom`, `/executions` |
| Governance | `/frameworks`, `/assessments`, `/assessments/{id}/controls/{control_id}` |
| Risk/actions | `/risks`, `/findings`, `/actions` |
| Evidence | `/evidence`, `/evidence/{id}/download`, `/attest`, `/verify`, `/evidence/export` |
| Runtime | `/policies`, `/guardrails/evaluate`, `/runtime/events` |
| Integrations | `/integrations`, `/integrations/{id}/config`, `/health` |
| Administration | `/memberships`, `/tenants`, `/settings`, `/audit`, `/audit/verify` |
| Reporting | `/dashboard`, `/reports`, `/reports/export?format=json` |

All resource IDs are opaque strings. List endpoints currently return arrays capped at1000 records; production-scale pagination is a remaining release item. POST returns201 for created resources and202 for queued jobs. PATCH merges allowed resource fields; policy PATCH accepts the complete typed policy. Cross-tenant references are rejected. Integration adapters accept only their documented input/config schemas; never put shell commands or private keys in them.

Execution states: queued → running → succeeded/failed, or cancelled. Cancelling a running subprocess requests termination through the adapter callback. Bounded HTTP calls may return before cancellation takes effect; completed output is discarded for a cancelled job. Worker interruption requires deliberate retry, and automatic replay is avoided. Retrieve `/executions/{id}` for raw output, normalization, logs, hashes and provenance.

Runtime evaluation requires an enabled explicit policy_id and text up to32000 characters. Native checks return `decision`, optional `sanitized_text`, check timings and `latency_ms` for check computation. The stored event omits input and output text. Full HTTP latency must be measured by clients; see benchmark records. Model/service adapter results are asynchronous execution results, not implicitly part of this synchronous pipeline.

Errors use FastAPI's `detail` field with401/403/404/409/413/422/429/503 as appropriate. Clients should not automatically retry non-idempotent creation. Idempotency keys, webhook delivery and external SSO/service-token management are not implemented and must be designed before a production Guardrail Sovereign connection.
