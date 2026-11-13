# Independent API contract

Base: `/api/v1`, release 0.2.0. OpenAPI is served at `/api/v1/openapi.json`;
interactive docs at `/api/v1/docs`. The checked-in docs/openapi.json matches the
code. No Guardrail Sovereign database or internal API is accessed.

POST /auth/login accepts email/password and returns a revocable opaque bearer
token. Tenant routes require Authorization: Bearer <token> and X-Tenant-ID.
GET /auth/me lists memberships. POST /auth/logout revokes one session;
POST /auth/password verifies current_password, accepts new_password (12?1024
characters), and revokes all sessions. Tokens expire after SESSION_HOURS (default 8).

| Area | Routes / behavior |
|---|---|
| Inventory | /systems, /bom, /bom/{id}/export; structural CycloneDX import and restricted cdxgen execution |
| Assessments | /frameworks, /frameworks/crosswalks, /assessments, /assessments/{id}/controls/{control_id}, /assessments/{id}/history, /assessments/{id}/export |
| Governance | /governance-records (optional framework filter), PATCH /governance-records/{id}; linked system/assessment/risk/evidence |
| Risks/actions | /risks, /findings, /actions |
| Evidence | /evidence, /evidence/{id}/download, /evidence/{id}/attest, /evidence/{id}/verify, /evidence/export |
| Policy history | /policies, PATCH /policies/{id}, GET /policies/{id}/versions, POST /policies/{id}/rollback with revision |
| Runtime | POST /guardrails/evaluate, /runtime/events, /runtime/reviews, PATCH /runtime/reviews/{id} with resolution, notes and owner |
| Integrations | /integrations, PUT /integrations/{id}/config, POST /integrations/{id}/health |
| Executions | /executions, /executions/{id}, POST /executions/{id}/cancel and /retry |
| Administration | /memberships, PATCH/DELETE /memberships/{user_id}, /tenants, /settings, /audit, /audit/verify |
| Reports | /dashboard, /reports, /reports/export?format=json |

Most resource lists accept limit (1?500, default 100) and offset (0?1,000,000);
headers X-Total-Count, X-Page-Limit and X-Page-Offset expose pagination.
Small catalogue/membership/history responses are not paginated. Search in the UI
filters loaded rows. IDs are opaque and cross-tenant lookups/references are denied.
POST returns 201 for creation or 202 for jobs; a successful DELETE returns 204.

Versioned records return version. Supply If-Match on edits/rollbacks to reject
stale writes with 409. Policy PATCH accepts the full policy model. Rollback saves
the previous state and creates a new version; history is not erased.
Idempotency-Key (8?100 alphanumeric/underscore/hyphen characters) is supported on
systems/risks/findings/actions and execution creation. Keys are scoped by tenant
and resource kind; reusing one with different input returns 409.

Jobs transition queued ? running ? succeeded/failed or cancelled. A retry creates
a new job and uses current enabled configuration. Terminal Presidio input is
removed, so a new input submission is required. Worker lease expiry is ten
minutes; reconciliation polls every 30 seconds. Redis notifications are advisory.

Runtime input is 1?32,000 characters and requires an enabled policy_id. Optional
system_id provides OPA risk classification; direction is input or output.
Policy checks select native/presidio/opa, executed in that order. Presidio requires
tenant enablement and private service configuration. Native redactions are passed
to Presidio; its output must match replacement of validated ranges. OPA can still
block original PII presence. Exceptions apply error_action=block/review.
latency_ms measures checks before persistence; only client roundtrip benchmarks
measure authentication, database/event/audit persistence and HTTP.

Events omit original/sanitized text. Human-review decisions do not replay or
release the original request. Contributors can edit draft governance resources
but cannot approve/close governance records or resolve reviews. Viewers/auditors
cannot mutate resources. Membership/config/settings require organisation_admin;
tenant creation requires platform_admin. The last administrator cannot be removed.

Errors use detail and appropriate 401/403/404/409/413/422/429/503 status codes.
The Redis quota is 600 requests per identity/minute across that identity's tenants,
plus separate login limits. Webhooks, OIDC, invitations and long-lived service
tokens remain unimplemented.
