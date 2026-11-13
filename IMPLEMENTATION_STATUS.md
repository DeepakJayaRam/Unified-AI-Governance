# Implementation status — v0.2.0

The interrupted v0.2 implementation was resumed in the original repository on
release/harden-v0.2. Commit 06679f0 and checkpoints/local-v0.1 are preserved.
Before changes, a working-tree ZIP, binary patch, Git bundle and ignored-file
inventory were saved under tmp/resume-checkpoint-20261113. No reset, clean,
force push, volume deletion or Guardrail Sovereign modification was used.

## Current verification

- Backend in the service-enabled Linux test container: **55 passed**, no skips.
  This includes real OPA, Presidio and cdxgen. Native Windows: **51 passed,
  4 service tests skipped**; those four passed in the container run.
- Frontend: **7 unit tests passed**, TypeScript/format/production build passed.
  **9 browser tests passed** against Docker, including all 21 pages, governance,
  signing/downloads, policy history/rollback, human review, account/password/role
  management, integrations, discovery, risk/findings/actions and settings.
- Automated axe WCAG 2 A/AA and 2.1 AA checks passed on login and seven workspace
  pages. This is not a full manual accessibility conformance certification.
- Real PostgreSQL 18.6: **13 isolated migration/RLS/audit checks passed**.
  Deployed uag_app is NOSUPERUSER/NOBYPASSRLS, migration 0002 is applied, and
  unscoped/foreign rows are denied. Redis and worker restart/recovery passed.
- Authenticated HTTP benchmark: **100 samples per case, five warmups**.
  Native + Presidio + OPA p99: short safe **85.8 ms**, short PII **91.6 ms**,
  near-limit **879.9 ms**. Includes PostgreSQL event/audit persistence.
- Python and both npm dependency audits report **zero known vulnerabilities**.
  Runtime image findings and explicit residual-risk analysis are retained in
  docs/release/SECURITY_REVIEW.md; zero container vulnerabilities is not claimed.
- All 25 upstream entries were rechecked: **5 tested executable**, **5 reference**,
  **11 deferred**, **4 restricted pending licence review**. Restricted source
  and model weights are not bundled.

See [full verification](docs/release/VERIFICATION.md), raw reports, and the
[v0.2 release notes](docs/release/v0.2.0.md). GitHub Actions and release metadata
provide remote evidence for the tagged commit. The historical v0.1 status is
archived in docs/release/v0.1-implementation-status.md and is superseded here.

## Work completed after reconnection

Presidio output is now constrained to detected-span replacements; malformed
responses cannot restore earlier redactions. HTTP failure/timeout regression
tests were added. Browser defects in text contrast, literal record titles and
assessment dialogs reopening during saves were fixed. Worker retries are
available in the UI. The release suite covers previously untested operations.

Runtime package managers and their vulnerable bundled libraries were removed;
zlib was patched; PostgreSQL's old privilege helper was replaced with pinned
su-exec. Presidio uses bundled public-suffix data with no runtime downloads.
Migration service health now reflects its one-shot exit status. Build contexts
exclude secrets, browser traces and generated outputs. Private GitHub
vulnerability reporting is enabled.

## Remaining scope limits

No public application hosting, cloud/VM verification, external penetration test,
backup/restore disaster-recovery drill, SSO/invitations, automatic retention or
notification delivery, managed key service, immutable external audit anchoring,
Envoy enforcement, Cosign, NeMo or Llama Guard execution is claimed. English
Presidio and native patterns are limited detectors. Governance checklists are
original assessment aids, not reproduced standards or legal/certification
determinations. Production operation requires environment-specific review.
