# Frontend verification — 2026-11-13

Environment: Windows, Node.js 24.13.0, npm 11.21.1, Next.js 16.4.6, React 19.3.1 and installed Google Chrome 157.0.8103.51. Tests used the independent application on `127.0.0.1:3100`, FastAPI on `127.0.0.1:8100`, an isolated SQLite database under ignored `temp/frontend-e2e`, and generated test-only credentials. The pre-existing application on ports 3000/8000 was left untouched.

| Check                                                          | Observed result                                                                                                                                                                                                                                                                                             |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm.cmd install --ignore-scripts` and final dependency update | npm audit reported **0 vulnerabilities** (64 packages in final install)                                                                                                                                                                                                                                     |
| `npm.cmd test`                                                 | **7/7 passed**, including tenant/auth headers, cookie omission, session expiration, authorization denial and validation handling                                                                                                                                                                            |
| `npm.cmd run typecheck`                                        | **Passed on final formatted source**. The layout test initially exposed a missing `@types/react-dom` dependency; verified 19.3.0 is now pinned.                                                                                                                                                             |
| `npm.cmd run build`                                            | Optimized Next.js production build passed with dynamic routes, nonce CSP proxy and standalone output                                                                                                                                                                                                        |
| Initial `npm.cmd run test:e2e` with real API credentials       | **2/2 passed**: responsive login and real login → inventory create → evidence create/integrity verify → policy create/PII sanitize → audit → logout                                                                                                                                                         |
| Expanded `npm.cmd run test:e2e`                                | **2/3 passed**. Login and all-21-page navigation passed. The longer workflow successfully persisted three framework assessments with evidence links, guardrail decisions and tenant-switch isolation, then failed the mobile viewport overflow assertion.                                                   |
| Mobile overflow fix                                            | A visually hidden, absolutely positioned table heading escaped its scroll container. Adding a containing block to `.table-scroll` fixes the overflow while retaining horizontal table scrolling.                                                                                                            |
| `npm.cmd run test:e2e -- layout.spec.tsx`                      | **1/1 passed after the fix** using the actual React Table component rendered to markup and actual application CSS in Chrome, without an application server. Asserted 390px document width and reachable off-screen table actions.                                                                           |
| Final production startup / complete expanded browser rerun     | **Blocked**: automatic approval review rejected `npm.cmd start`, including after native scripts were restricted to loopback, with reason `blocked by policy`. No alternate runner was used. The complete expanded browser suite has therefore **not been confirmed passing on the final production build**. |
| Docker startup                                                 | Not executed by this frontend task; see root deployment verification for the host Docker blocker.                                                                                                                                                                                                           |

The later browser signing assertions (`E2E_SIGNING_ENABLED=1`) were added but have not run because production startup was rejected. Backend signature tests and HTTP workflow verification are reported separately by the backend task. No browser-based signing success is claimed here.

Desktop application screenshots from the genuine browser workflow were inspected for layout. Playwright cleaned those transient outputs during the later isolated test run. The retained screenshot is `test-results/mobile-layout-regression.png`, explicitly a synthetic layout regression fixture, not a live dashboard or integration result. `test-results/` is ignored by Git.

Frontend source is formatted with Prettier 3.10.1, verified from the official npm registry. No integration credentials or session tokens are in source or browser persistent storage. Default native listeners are loopback-only; Docker binds its private container port separately.

## Re-run after local server startup is available

Run backend migrations and bootstrap an isolated test tenant as described in the root deployment guide. Set the public API URL before building. Supply credentials through environment variables without printing them:

```powershell
$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8100/api/v1'
npm.cmd run build
npm.cmd start
```

In a separate terminal with test-only `E2E_EMAIL` and `E2E_PASSWORD` already set:

```powershell
$env:E2E_BROWSER_CHANNEL='chrome'
npm.cmd run test:e2e
```

Set `E2E_SIGNING_ENABLED=1` only when the isolated API has a valid `SIGNING_KEY_PATH`. The layout regression can run independently of API/frontend servers with `npm.cmd run test:e2e -- layout.spec.tsx`.
