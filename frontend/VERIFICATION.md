# Frontend verification

v0.2: seven unit tests, TypeScript, Prettier and Next.js production build pass.
Nine Playwright tests pass against the actual Docker API, PostgreSQL and worker.

Coverage includes all 21 pages and seven workspaces; exact record-title
preservation; inventory/evidence/signing/downloads; three framework assessments,
history/export/completion; governance records; policy rollback/human review;
membership roles, password rotation, denied viewer writes and access removal;
integration enablement/health, real worker failure/retry and cdxgen discovery;
risk/findings/actions, settings, responsive layout and automated accessibility.

Axe WCAG 2 A/AA and 2.1 AA scans pass on login and seven workspace pages. This is
automated coverage, not a full manual conformance audit. Next's streamed page
title is awaited before scanning. Sessions are memory-only and tests use
synthetic accounts. The suite runs with one worker to isolate shared fixture
state. Benchmarks run separately.

Windows verification uses Edge Chromium 157.0.4341.46 through Playwright 1.65.0.
CI installs Playwright Chromium. Set E2E_EMAIL/E2E_PASSWORD and
E2E_SIGNING_ENABLED=1 when running the suite directly; scripts/release_checks.py
loads the ignored release identity. Browser traces/screenshots are ignored
because they can contain authenticated data. Raw summaries are in docs/release.
