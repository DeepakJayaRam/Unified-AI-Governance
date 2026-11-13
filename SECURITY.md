# Security

Report suspected vulnerabilities privately to the repository owner's security contact (configure a GitHub private vulnerability reporting channel before publication). Do not put tenant data, prompts, tokens or signing keys in public issues.

Security controls implemented: Argon2id passwords, revocable hashed bearer sessions, role checks, tenant-qualified resource queries, PostgreSQL FORCE RLS for tenant records and audit events, validated cross-resource references, bounded request/evidence/adapter input, deny-by-default adapter configuration, shared Redis production rate limits, output encoding, CORS allowlist, CSP/security headers, non-root resource-limited containers and explicitly configured guardrail error decisions.

Browser tokens are held in memory and are never cookies, so ambient-cookie CSRF does not apply. XSS remains a threat; render data as text, retain CSP and avoid raw HTML. Use HTTPS for all deployments outside loopback. Never use database owner credentials in the API/worker. Do not expose PostgreSQL/Redis/OPA to public networks.

The native detector checks email, US SSN and payment-card-like digit patterns and configured literal terms only. It is not comprehensive PII detection, prompt-injection detection, a legal classifier, or a replacement for evaluated model guardrails. Disable a policy explicitly; an evaluation error yields its declared block/review decision.

Evidence content and raw tool results can contain confidential information. Limit membership and export access. Configure encrypted disks/backups and secret-manager key injection. Hash chaining detects changes against a trusted checkpoint; a privileged database operator can rewrite history or drop protective triggers. External immutable storage and trusted timestamping are not implemented. Key rotation/trust history needs an operator procedure before long-term signature preservation.

The subprocess wrapper bounds output/time and does not invoke a shell. cdxgen additionally uses Node's permission model and rejects package scripts/local paths. These are defence layers, not a kernel sandbox. Use isolated worker containers with restricted egress and resource limits. Do not run arbitrary source repositories or install scripts through a tenant request.

Dependency procedure: pinned direct dependencies, transitive Python/npm locks and image digests; CI audits Python/npm and rebuilds containers. Review advisories weekly, update in a branch, re-run tenant/migration/adapter/browser tests and record actual changed upstream licences. Never override an advisory without a documented exploitability analysis and expiry date. Production release additionally requires independent penetration testing, restore drill, operational alerting, trusted key lifecycle and load/concurrency tests against the target workload.
