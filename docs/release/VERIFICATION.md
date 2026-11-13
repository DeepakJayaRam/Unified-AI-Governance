# v0.2 release verification — 2026-11-13

## Preserved state and changes

Original commit: `06679f0b65d250579afd2c83cb90010b9c135dae`, preserved by
`checkpoints/local-v0.1`. Work continued on `release/harden-v0.2` in the original
workspace. Pre-edit ZIP/patch/Git bundle: ignored `tmp/resume-checkpoint-20261113`.
No reset, clean, force push, volume deletion or Guardrail modification occurred.

The interrupted work was retained. Added verification exposed and fixed
anonymizer output restoration, literal-title formatting, text contrast and an
assessment-close/save race. Retry UI, private suffix data, safer runtime images,
accurate integration classifications and release documentation are complete.

## Verification types and actual results

| Verification | Result | Evidence |
|---|---|---|
| Backend Windows unit/local integration | 51 passed; four service tests intentionally skipped here | backend-local.txt |
| Backend Linux with real services | 55 passed, zero skips | backend-services.txt |
| Real OPA | version 1.22.4; allow/block/review and rejected compilation; adapter failure behavior | backend-services.txt, environment.json |
| Real Presidio | 2.2.366 + spaCy 3.8.18/model 3.8.0; detection, anonymization, malformed request rejection, prior redactions | backend-services.txt, presidio-installed.json |
| HTTP fault injection | Real loopback HTTP failures, timeout, malformed offsets/OPA response and malicious anonymizer output | tests/test_http_failures.py; backend-services.txt |
| Parser/pipeline doubles | Explicitly marked unit tests; not upstream success evidence | tests/test_hardening.py, tests/test_security_adapters.py |
| cdxgen / Trestle / DSSE | Actual CLI, upstream OSCAL models and Ed25519 operations including tampering/trust rotation | backend-services.txt, compose-workflow-v0.2.json |
| Frontend units / type / style / build | 7 tests passed; TypeScript, Prettier and Next production build passed | frontend-*.txt |
| Browser | 9 passed; Edge Chromium 157.0.4341.46/Playwright 1.65.0 against Docker | browser.txt |
| Accessibility | axe WCAG 2 A/AA and 2.1 AA: login + seven pages passed; not manual certification | browser.txt; frontend/tests/e2e/accessibility.spec.ts |
| PostgreSQL migrations/RLS | 13 isolated real checks; deployed role/RLS/migration verified | ../validation/postgres.json, recovery.json |
| Redis / worker / persistence | restart survival, lost notification recovery, cancellation/retry and synthetic expired lease | recovery.json |
| Concurrent tenant operations | Five-tenant HTTP isolation and concurrent cdxgen idempotency passed | compose-workflow-v0.2.json |
| Rate limiting | 600 HTTP successes + 20 expected 429s; independent identity still succeeds | recovery.json |
| Docker | Seven running services healthy; migration exit 0; existing volumes retained | environment.json |
| Dependencies / licence / secrets | Python/npm audits clear; 25 sources rechecked; image residuals disclosed; Gitleaks clear | SECURITY_REVIEW.md; audit/scan reports |

Worker expiry uses an explicitly injected eleven-minute-old synthetic running
lease; it tests the real recovery code without pretending eleven minutes of
unobserved execution occurred. HTTP error servers are fault injection, not mock
replacements for the real Presidio/OPA success tests. Redis and PostgreSQL are
actual deployment services, not in-memory doubles.

## All seven workspace results

| Workspace | Verified result |
|---|---|
| 1 Discovery/inventory | System forms, real restricted cdxgen CLI/worker, CycloneDX persistence/export and tenant separation passed |
| 2 EU AI Act | Classification/obligation records, assessment/evidence links, history/export and approval rules passed |
| 3 ISO/IEC 42001 | Management-review records, controls/evidence/history/export and complete/reopen passed; original checklists only |
| 4 NIST AI RMF | Risk-treatment records, risks/findings/corrective actions, evidence links and framework assessment passed |
| 5 Evidence/OSCAL | Original downloads, actual Trestle validation, DSSE signing/verification/tampering and key trust passed |
| 6 Runtime | Real OPA decisions, policy history/rollback, metadata-only events, human-review resolution and audit passed |
| 7 LLM guardrails | Native and real Presidio pipeline, disabled-control behavior, failure/timeout handling and composed redactions passed |

Browser navigation covers 21 pages; state-changing tests cover the implemented
workflows above. This is meaningful functional coverage, not an assertion that
every possible field combination or attack has been exhaustively tested.

## Authenticated HTTP performance

AMD Ryzen 7 5700U, 16 logical CPUs, Windows 11 + Docker Desktop Linux amd64.
Five warmups and 100 measured sequential samples per case. Dedicated benchmark
identity; no browser suite ran concurrently. Pacing occurs outside timed samples.
Existing unrelated services remain running. Container resource limits apply.
Includes bearer auth, membership, Redis rate limiting, PostgreSQL RLS, selected
checks, event/audit persistence and loopback HTTP. Excludes TLS ingress/WAN/cloud.
Raw distributions: benchmark-v0.2.json; machine/container details: environment.json.

| Pipeline/input | Characters | Decision | Samples | p50 ms | p95 ms | p99 ms |
|---|---:|---|---:|---:|---:|---:|
| native/short_safe | 26 | allow | 100 | 30.41 | 44.75 | 66.09 |
| native/short_pii | 26 | sanitize | 100 | 30.79 | 42.34 | 49.93 |
| native/near_limit | 31993 | sanitize | 100 | 34.52 | 48.12 | 52.77 |
| complete/short_safe | 26 | allow | 100 | 47.52 | 63.72 | 85.83 |
| complete/short_pii | 26 | block | 100 | 46.70 | 75.97 | 91.57 |
| complete/near_limit | 31993 | block | 100 | 659.37 | 834.54 | 879.92 |

The complete pipeline runs native → Presidio → OPA. OPA blocks original PII
presence even after redaction. No sub-50 ms end-to-end claim is made. Near-limit
NLP is materially slower. The earlier 429-interrupted run is preserved unchanged
as compose-verification-concurrent-rate-limit.json; it is not a successful run.
The prior completed four-pipeline run remains compose-verification.json and
measures a different input mix.

## All 25 integration decisions

The authoritative numbered table is [INTEGRATION_REGISTER.md](../../INTEGRATION_REGISTER.md).
Tested executable: 1 cdxgen, 15 Trestle, 17 in-toto/DSSE, 19 OPA, 23 Presidio.
Reference-only: 8 Awesome EU AI Act, 9 ISO toolkit, 12 NIST AIRC, 13 M3,
14 OSCAL Compass. Deferred: 2 OWASP AIBOM, 4 RiskForge, 5 AbdelStark toolkit,
6 Venturalitica, 7 COMPL-AI, 11 AI Atlas Nexus, 16 Cosign, 18 aigrc,
20 Envoy, 21 AI Verify, 24 NeMo. Licence-restricted pending review: 3 OpenComplAI,
10 unlicensed EU compliance toolkit, 22 VerifyWise, 25 Purple Llama/models.
No adapter-only or unsupported entry is claimed. OPA-Envoy is deferred within 19.
All 25 sources and the OPA-Envoy reference were rechecked; no restricted source
or weights are bundled. Model training-source notices are preserved separately.

## Limits and remote release evidence

See SECURITY_REVIEW.md and ../../DEPLOYMENT.md. This is a reproducible public
source release with tested local deployment, not public application hosting or
production certification. Cloud operation, disaster recovery, external penetration
testing, SSO/invitations and deferred integrations remain outside tested scope.

Repository: https://github.com/DeepakJayaRam/Unified-AI-Governance
Release: https://github.com/DeepakJayaRam/Unified-AI-Governance/releases/tag/v0.2.0
Actions: https://github.com/DeepakJayaRam/Unified-AI-Governance/actions
The GitHub tag/release and corresponding Actions run identify the published
commit. Final publication is verified separately after pushing; local reports
alone are not proof of remote publication.
