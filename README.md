# Unified AI Governance & Security

An independent, API-first governance application with seven connected workspaces: discovery, EU AI Act assessment support, ISO/IEC 42001 management workflows, NIST AI RMF, evidence/OSCAL, runtime policy, and LLM guardrails.

This repository contains a working FastAPI/Next.js application, not copies of 25 upstream projects. Every supplied entry is researched in the [integration register](INTEGRATION_REGISTER.md). Executable adapters, external services, reference resources, deferred integrations and licence restrictions are distinguished in the interface. See [implementation status](IMPLEMENTATION_STATUS.md) for exact test results and release blockers.

## Run locally on Windows

Requirements: Python 3.14, Node 24 LTS, npm and Git. cdxgen's tested toolchain is Node 24.22.3 (minimum 24.15). PostgreSQL/Redis are used by Compose; SQLite and in-process background work support single-process development.

From the repository root in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uag.cli bootstrap --email admin@example.org --tenant "My organisation"
```

The bootstrap command prompts for a password of at least 12 characters. It never replaces an existing identity. No demo account or production password is embedded. Then run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn uag.main:app --host 127.0.0.1 --port 8100 --no-access-log
```

In a second terminal:

```powershell
cd frontend
npm.cmd ci --ignore-scripts
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8100/api/v1"
npm.cmd run dev
```

Open **http://127.0.0.1:3100**. API docs: **http://127.0.0.1:8100/api/v1/docs**. Ports are deliberately separate from an existing service found on port 3000. Refreshing the page requires logging in again because browser tokens stay in memory.

For Linux/macOS use `python3.14`, `.venv/bin/python` and `npm`, and export environment variables in your shell. The `.env` file is consumed by Docker Compose; native Python reads process environment variables, not `.env` automatically.

## Configure real integrations

Install discovery tooling from `integrations/tooling` with `npm ci --ignore-scripts --omit=optional`. Use a supported Node executable; an administrator may set `UAG_NODE_EXECUTABLE` to its absolute path. In the catalogue, configure/enable cdxgen with `{}` and run a health check. Submit a system scan with **both** `package_json` and npm v3 `package_lock` JSON objects. Scripts, local/git dependencies and arbitrary host paths are rejected. This is lockfile inventory, not general source scanning or vulnerability detection.

cdxgen secure mode requires a staging path **without spaces**. If your Windows TEMP path has spaces, create a dedicated empty directory such as `D:\uag-scan-temp` and set `$env:UAG_SCAN_TMP_ROOT = 'D:\uag-scan-temp'` in the API terminal. The directory is operator-controlled, checked by health, and contains only automatically cleaned per-job manifests. Docker's `/tmp` needs no override.

Compliance Trestle validates actual supported OSCAL JSON models. in-toto workflows generate statements and optionally DSSE signatures. Provision a key with `uag keygen --path secrets/evidence-signing.pem` and set `SIGNING_KEY_PATH` before starting the API/worker. Restrict Windows ACLs to the service identity. Signing is unavailable until configured; ordinary evidence hashing works without a key.

OPA and Presidio connect only to operator-configured service URLs. Tenant forms cannot set arbitrary URLs, commands or tokens. NeMo, Llama Guard, Cosign and other entries without tested adapters remain clearly marked as awaiting integration/configuration or reference-only. Read [integration operations](THIRD_PARTY_INTEGRATIONS.md) and the [licence audit](LICENCE_AUDIT.md), especially before using VerifyWise or OpenComplAI.

## Working workflows

- Create an AI system; create a framework assessment; attach evidence to controls; track risks/findings/corrective actions; export a JSON report.
- Import CycloneDX inventory and compare component identities between imports; or queue a restricted cdxgen scan, inspect raw output/provenance and view the generated BOM.
- Add validated text/JSON/XML/CSV evidence, download original content, attest with a configured key, verify integrity/signatures and export an evidence package.
- Create an explicit policy; evaluate an input; observe allow/block/sanitize/review results and per-check latency. Runtime history stores decision metadata without the prompt or sanitised text.
- Create additional tenant workspaces as platform administrator and add tenant members with explicit roles. Auditors and viewers are read-only.

The framework checklists are original application support material. They do not reproduce the ISO standard, determine legal compliance, or guarantee certification. The legal references include the current sources recorded in `docs/research`; no unverified regulatory deadline is hardcoded.

## Verify and deploy

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\benchmark.py
# In frontend/: npm test -- --run; npm run build
```

Real adapter and browser tests have additional setup described in `docs/validation` and `frontend/README.md`. Synthetic test workspaces are isolated from application data. Benchmark results identify their environment and measured scope; the sub-50 ms end-to-end target is not assumed.

Docker/cloud instructions, migrations, key handling, backups and troubleshooting: [DEPLOYMENT.md](DEPLOYMENT.md). API consumer contract for future independent integration: [docs/API.md](docs/API.md). Security limits and reporting: [SECURITY.md](SECURITY.md). No Guardrail Sovereign integration or GitHub publication has been performed.
