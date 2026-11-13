# Architecture

The engine exposes `/api/v1` REST endpoints independently of Guardrail Sovereign. FastAPI owns authentication, tenancy, governance resources and execution orchestration. Next.js renders persisted data; no demonstration metrics are seeded. PostgreSQL is the deployment database; Redis carries job notifications. A worker retrieves tenant-scoped jobs and runs only registered adapters. SQLite is an explicit development alternative.

## Boundaries

- `backend/uag`: identity, persistence, API schemas and module routers.
- `integrations`: research-backed catalogue and typed execution adapters. Reference entries cannot execute.
- `frontend`: session-only web client, navigation, forms and resource views.
- `migrations`: Alembic revisions including PostgreSQL row-level security.
- `tests`: contracts, isolation, workflows, adapters and measured runtime performance.
- `docs/research`: inspected upstream evidence and licence audit inputs.

## Tenant isolation

Users are global identities and memberships grant an explicit role in a tenant. Each authenticated request must select a membership through `X-Tenant-ID`. Tenant resources include their tenant identifier in every query and mutation. Cross-resource references are checked within that tenant. PostgreSQL RLS adds database enforcement when using the non-superuser application role. Administrative bootstrap/migrations use separate privileged credentials. Sessions are random opaque tokens; only token hashes are stored. Passwords use Argon2id. Auditors/viewers cannot mutate resources.

## Governance data

Typed API models validate versioned tenant document records for inventory, BOMs, risks, findings, corrective actions, assessments, evidence, policies and settings. JSON document storage supports varied upstream output without fabricating a common meaning; resource kind and indexes preserve module separation. Raw outputs are retained alongside parsed results and provenance. Assessments use original application checklists with authoritative references, not reproduced ISO standard text or claims of certification.

## Evidence and audit

Evidence stores bytes in a tenant-scoped record with media type, size and SHA-256. Downloads use attachment disposition and `nosniff`. Audit events are append-only through the API and hash chained. This is tamper-evident application history, not immutable storage against a database administrator. Signing requires a separately provisioned private key; the frontend never receives it. Format/schema verification is distinct from cryptographic authenticity and from legal compliance.

## Runtime and integration trust

Fast local checks produce explicit allow/block/sanitize/review decisions and measured latency. They do not claim the coverage of Presidio, NeMo or Llama Guard. Remote/model checks run only when configured; failure behaviour is a policy field. Adapters use typed inputs, allowlisted executable paths/arguments, deadlines and bounded output. Arbitrary commands and user-selected URLs are not accepted. Service URLs are deployment-controlled to limit SSRF. Adapters never infer successful configuration from catalogue presence.

## Deployment and future consumers

Compose separates frontend, API, worker, PostgreSQL and Redis. TLS terminates at a configured ingress. API tokens remain tenant scoped through membership, so future consumers can use the same OpenAPI contract without internal database access. Cloud operators must supply TLS, secret storage, backups, network policy and monitoring. Future Guardrail Sovereign integration requires a separate request.

## v0.2 concurrency and review

PostgreSQL advisory locks serialize tenant quotas, idempotency and the audit chain. Record versions and If-Match prevent lost edits. Policy and assessment history save prior snapshots; rollback produces another version. Governance records link decisions to systems, framework assessments, risks and evidence. Human reviews contain decision metadata and operator notes, without retained synchronous prompts or automatic replay.

Native, Presidio and OPA checks compose in a fixed order. Presidio receives prior sanitized text; the adapter validates the returned replacement spans. Synchronous timing ends before event/audit persistence, so it is explicitly distinct from measured HTTP roundtrip latency. Async Presidio inputs are temporarily persisted until terminal state and then removed. Redis notification loss is recovered from PostgreSQL; expired running leases require manual retry.
