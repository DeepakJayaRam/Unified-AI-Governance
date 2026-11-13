# Frontend

Next.js application for the versioned governance API. All workspace data comes from the backend; dashboard values and empty states are not seeded or fabricated.

## Run

Requires Node.js 24. Set `NEXT_PUBLIC_API_URL` to the API base URL before building (default `http://localhost:8100/api/v1`). The API must allow the frontend origin in its CORS configuration.

```powershell
npm.cmd ci
npm.cmd run dev
```

The native server binds only to `127.0.0.1:3100`. Production: `npm.cmd run build` and `npm.cmd start`. Docker uses the standalone Next.js output on container port 3000, published separately on host port 3100. Frontend API URL is a public build-time setting, never a place for secrets.

Accounts are provisioned by the backend bootstrap CLI. Bearer tokens are held only in React memory and cleared on reload, sign-out or an authentication failure. Requests explicitly omit cookies. Tenant switching reconstructs page state and refetches tenant data. Authorization is enforced by the API.

## Verification

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

The authenticated browser tests run against a real backend and create records. Set `E2E_EMAIL` and `E2E_PASSWORD` to an isolated test tenant platform administrator. Without them the authenticated tests are explicitly skipped; only the login rendering test runs. Do not run mutating browser tests against production workspaces. `E2E_BASE_URL` defaults to `http://127.0.0.1:3100`. For local tests, set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8100/api/v1` before building and allow that frontend origin in backend CORS. Set `E2E_BROWSER_CHANNEL=chrome` to use an existing Chrome installation rather than downloading Chromium. With a server signing key configured, set `E2E_SIGNING_ENABLED=1` to exercise Ed25519 attestation and signature verification in the browser.

Browsers and npm may use the system temporary directory. On a space-constrained Windows C: drive, set `TEMP`, `TMP` and `PLAYWRIGHT_BROWSERS_PATH` to a dedicated development directory on a drive with capacity; do not delete unrelated application data.

Versions were queried from the official npm registry on 2026-11-13 before selection: Next.js 16.4.6, React 19.3.1, TypeScript 7.0.2, Vitest 5.1.0 and Playwright 1.65.0. Exact transitive versions are locked by `package-lock.json`.

## Interfaces

Routes cover inventory, discovery, CycloneDX import, three framework assessments, risks, findings, corrective actions, evidence, OSCAL/attestations, guardrails, runtime decisions, catalogue/configuration, execution history, audit, reports, membership and settings. JSON adapter forms intentionally use backend validation because integration schemas vary. Reference-only, deferred and licence-blocked entries have no configure control.

Governance assessments are decision support; the interface does not claim legal compliance or certification. Artifact hashes and unsigned attestations are presented distinctly from digital signatures. Runtime latencies are individual observations, not percentile benchmarks.
