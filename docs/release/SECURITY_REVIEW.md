# v0.2 security review — 2026-11-13

Scope: original application, locked dependencies, six runtime images, Compose
configuration, API isolation, real services, browser workflows and local deployment.
This is engineering verification, not an independent penetration-test certificate.

## Findings and dispositions

Python requirements audit and both npm lockfile audits report zero known
vulnerabilities. The initial image scan found additional vulnerabilities in
vendored pip/npm tooling, Debian zlib and PostgreSQL's old Go-built gosu.
Runtime pip/npm were removed, zlib was upgraded to the exact Debian security
revision, and gosu was replaced with Alpine su-exec 0.3-r0. Tests and restart
verification were rerun. Original scanner output is preserved under ignored
tmp/; current full reports are adjacent to this document.

| Runtime image | Critical | High | Medium | Low | Unknown |
|---|---:|---:|---:|---:|---:|
| API / worker (same backend build) | 0 | 47 | 89 | 65 | 4 |
| Presidio | 0 | 47 | 89 | 65 | 4 |
| PostgreSQL | 0 | 0 | 0 | 0 | 0 |
| Frontend | 0 | 0 | 1 | 0 | 0 |
| Redis | 0 | 0 | 1 | 0 | 0 |
| OPA | 0 | 1 | 1 | 0 | 0 |

Counts are package/advisory occurrences, not unique flaws; backend/Presidio share
a Debian base. No backend/Presidio Python-package or frontend npm-package
vulnerabilities remain in the final runtime scan. No scanner ignore/suppression
file was added. These are point-in-time database findings, not security guarantees.

## Residual high-severity analysis

The 47 Debian occurrences per Python image cover eleven distinct advisories.
Trivy lists no fixed Debian package version for them:

- util-linux CVE-2026-76642/78408/78409/78410 and ACL CVE-2026-54369 concern
  privileged mounts, cgroups or filesystem privilege operations. App services run
  as uid 10001/10002 with all capabilities dropped, no-new-privileges, read-only
  roots and no host filesystem/namespace access. Tenant input cannot invoke
  these utilities or select arbitrary paths.
- ncurses CVE-2025-69720 requires the affected terminal-processing path. The
  services are noninteractive HTTP/worker processes; tenant requests do not
  select terminal databases or invoke ncurses.
- SQLite CVE-2026-119373/119374/119379 affect FTS5 indexes or session changesets.
  Deployment uses PostgreSQL. The development SQLite schema does not use those
  extensions and no route accepts a SQLite file, SQL program or changeset.
- systemd-homed CVE-2026-16742 and Perl Archive::Tar CVE-2026-9538 are attributed
  through Debian source packages. The runtime image inspection found no
  systemd-homed executable or Archive/Tar.pm, and neither service is invoked.

OPA 1.22.4 contains golang.org/x/net HTML parser/renderer findings
CVE-2026-78661 (high, fixed upstream in 0.62.0) and CVE-2026-97045 (medium).
The deployment's pinned governance.rego consumes JSON risk/PII flags and invokes
no HTML parser/renderer. Tenant callers cannot upload Rego, select an endpoint
or expose the service directly; OPA is on the private network with no host port.
These vulnerable HTML paths are not reachable through this release's documented
adapter/policy. The official image is retained with the findings disclosed.

Release-scope disposition: the above findings have no identified reachable
vulnerable path through the tested, constrained application configuration.
They are not marked fixed. Reassess by **2026-12-13**, or immediately before
changing policies, adding raw database inputs/terminal processing, granting
privileges, mounting host paths or exposing internal services. Deployments must
perform their own threat/operational review. Public source release is permitted
within this scope; production certification is not claimed.

## Other security evidence

- Fifty-five backend tests include authorization, malformed input, tampering,
  key rotation/trust, stale edits, idempotency, service failures and privacy.
- Real PostgreSQL tests verify migration up/down/up, FORCE RLS, application
  role restrictions, foreign-row protections and append-only audit triggers.
- Concurrent HTTP quota testing returned 600 successes and 20 expected 429s;
  another identity still succeeded. Five-tenant API operations and concurrent
  cdxgen idempotency are verified separately.
- A malicious or malformed anonymizer output must match replacement of validated
  spans; it cannot restore earlier redactions or insert unrelated text.
- Git history and publication candidates are scanned with Gitleaks. Credentials,
  private keys, databases, node_modules, builds and browser traces are excluded.
  The initial final-candidate scan flagged the public Python release-signing
  fingerprint twice in Presidio image metadata. Redundant environment metadata
  and that build-history fingerprint were omitted from the published report;
  vulnerability findings are unchanged. Original output remains under ignored tmp/.
- Upstream records contain source URLs/hashes, not restricted source trees.
  All 25 sources/licences were rechecked. See LICENCE_AUDIT.md.
- Private vulnerability reporting is enabled on GitHub.

Operational limitations: no external penetration test, backup-restore drill,
cloud deployment, SSO/invitations, automatic retention/notifications, external
immutable audit anchoring or managed key service is claimed. Async Presidio
prompts exist in the database until terminal state; configure encryption and access controls.
Synchronous event records omit prompt/output text. Human-entered notes can still
contain personal information and must be governed by the operator.

Compose static scan reports one high finding for the PostgreSQL image starting as root. Its standard entrypoint must initialize volume ownership before dropping privileges. The observed database PID 1 UID is 70 (postgres), using su-exec, with no public database port. Other app images specify non-root users. This scoped initialization requirement is retained and must be reassessed if the entrypoint changes.
