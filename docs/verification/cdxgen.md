# cdxgen adapter verification

Run on 2026-11-13, Windows amd64, Python 3.14, Node 24.22.3. The portable
Node executable was fetched from the official distribution and checked against
the official SHASUMS256.txt; SHA-256:
`86fc4785327db5f5c7558dc6156c543b433c313e813a222e088086222ab4afa6`.
It lives in ignored `tmp/tools/node-v24.22.3`; no system Node was replaced.

Commands actually run and observed outcomes:

| Command | Observed result |
| --- | --- |
| `npm install --ignore-scripts --omit=optional --no-fund --no-audit` in integrations/tooling | Installed pinned cdxgen13.7.0; original host Node24.13 emitted dependency engine warnings. Execution was moved to supported24.22.3. |
| `node cdxgen.js --help` | cdxgen13.7.0 advertised all fixed flags used by adapter. |
| Restricted CLI with package.json only | Valid but empty BOM. Adapter therefore requires genuine package-lock input and does not claim manifest-only inventory completeness. |
| `npm audit --omit=optional --json` before overrides | Five moderate findings propagated from glob and minimatch; zero high/critical. |
| `npm install --ignore-scripts --omit=optional --no-fund --no-audit` with patched overrides | Patched glob14.0.6/minimatch11.0.8 installed, lockfile updated. |
| `UAG_TEST_CDXGEN=1 python -m pytest tests/test_discovery_adapter.py -q` | 11 passed, including actual cdxgen invocation and configured no-space staging from a workspace with spaces; one unrelated Starlette/httpx deprecation warning. |
| `python scripts/verify_cdxgen.py` | Succeeded; one openai6.8.1 component from synthetic fixture; exact raw BOM and provenance recorded in cdxgen-test.json. |
| `node npm-cli.js audit --omit=optional --json` after overrides | Exit0; zero vulnerabilities reported. |

The fixture is deliberately synthetic test data. It is not seeded into any
tenant and makes no claim about this repository's dependencies or client data.
The actual CLI command is retained with deployment/staging paths represented by
placeholders. Output format is generated and validated by upstream cdxgen.

The tested scope is npm v3 lockfile inventory only. Other languages, container
images, model analysis, source usage detection and remote services are not
enabled by this adapter. Dependencies' licence metadata is not a legal finding;
missing metadata creates only an informational review item.

An HTTP workflow run exposed an upstream restriction: cdxgen secure mode
rejects target paths containing spaces, even when invoked as `.` from that
directory. The adapter now checks the effective staging root during health
checks and reports Not configured until `UAG_SCAN_TMP_ROOT` names an existing
absolute directory without spaces. The actual regression test used
`D:\uag-scan-temp`, leaving workspace and user files unchanged.

The Node24.22.3 CLI invocation took about2.1seconds in this run. This is a
background workflow and carries no sub-50ms performance claim. Linux/Docker
startup, cgroup enforcement and network isolation need their own deployment
verification.
