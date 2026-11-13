# Implementation plan

Independent application; no Guardrail Sovereign source or database dependency. Publishing requires separate approval.

| Phase | Deliverable | Verification gate |
|---|---|---|
| 0 | Inspect workspace and tools; preserve existing files | Environment report |
| 1 | Verify 25 upstream entries and licence terms | Commit/source-based register; explicit uncertainty |
| 2 | API, tenancy, adapter and deployment architecture | Architecture and contract review |
| 3 | Reproducible backend/frontend foundation | Dependency installation |
| 4 | Authentication, migrations, tenant-scoped API | Auth, isolation and migration tests |
| 5 | Responsive, data-backed frontend | Production build and browser workflow |
| 6 | Registry, typed adapter contract and durable jobs | Registry and adapter tests |
| 7 | Verified feasible integrations; clear deferred states | Real commands and captured results |
| 8 | Assessment, risk, evidence and audit workflows | End-to-end API workflow |
| 9 | Explicit runtime policies and guardrails | Error decisions and latency tests |
| 10 | Security, frontend, API and performance tests | Recorded outputs; no false pass claims |
| 11 | Docker Compose, PostgreSQL, Redis and workers | Compose validation/start when daemon available |
| 12 | Independent cloud deployment and operations docs | Configuration review |
| 13 | Acceptance review, remaining blockers and release checklist | Status report with measured evidence |

Prioritise a working local vertical slice (system → assessment/scan → findings → evidence → report), then expand verified adapters. Reference resources are catalogue entries, not executable integrations. The research register must precede upstream adapter code. Native application controls are labelled separately from upstream tools.

Default decisions: Apache-2.0 for original application code; Python/FastAPI/SQLAlchemy/Alembic; Next.js/TypeScript; PostgreSQL/Redis in Compose; SQLite for explicitly documented single-process development and tests. No automatic public registration. A local bootstrap command creates the initial administrator with a user-supplied password. Bearer sessions are revocable and browser-memory-only. Production requires HTTPS at the ingress.
