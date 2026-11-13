# Deployment and operations

## Verified local deployment

v0.2 uses Docker Desktop Linux amd64 on Windows 11. API and frontend bind only
127.0.0.1:8100 and 127.0.0.1:3100. PostgreSQL, Redis, OPA and optional Presidio
have no published host ports. Guardrail Sovereign services are unrelated.
This is a public source release; no public application hosting is provisioned.

Prerequisites: Docker/Compose 2.24.4+, adequate disk and at least 8 GB available
memory. Presidio's hash lock targets CPython 3.12/Linux amd64. The application
uses Python 3.14; discovery uses Node 24.22.3 (minimum 24.15). Windows PATH also
contains Node 24.13.0; tests explicitly select
`D:\Unified AI Governance\tmp\tools\node-v24.22.3\node.exe` using
`UAG_NODE_EXECUTABLE`. Docker uses `/usr/local/bin/node`, version 24.22.3.

1. If `.env` does not exist, copy `.env.example`. Set independent random hexadecimal
   `POSTGRES_PASSWORD` and `APP_DB_PASSWORD`; keep this file private.
2. Run `docker compose config --quiet` and `docker compose build`.
3. Run `docker compose up -d --wait api worker frontend opa`.
4. Run `docker compose exec api python -m uag.cli bootstrap --email admin@example.org --tenant "My organisation"` and enter a new password.
5. Open http://127.0.0.1:3100 and verify http://127.0.0.1:8100/health.

Migrations run `alembic upgrade head` as `uag_owner`; API/worker use
`uag_app`, NOSUPERUSER/NOBYPASSRLS. Initialization runs only on a fresh volume.
Changing .env does not rotate existing passwords. Never remove volumes to repair
credentials. Migration 0002 adds optimistic versions and unique tenant/resource
keys. Back up before upgrading a non-test deployment.

The PostgreSQL image derives from pinned official 18.6 and replaces its old
Go-based gosu with Alpine su-exec 0.3-r0. The entrypoint initializes/chowns data
as root and runs PostgreSQL as its dedicated user. Engine files, data path and
volumes are unchanged. App containers have read-only roots/dropped capabilities;
pip/npm are removed from app runtime images. Zlib uses a pinned security revision.

## Optional Presidio and signing

Create the signing key once without overwriting an existing key:

```text
python -m uag.cli keygen --path secrets/evidence-signing.pem
docker compose -f docker-compose.yml -f docker-compose.presidio.yml -f docker-compose.signing.yml build
docker compose -f docker-compose.yml -f docker-compose.presidio.yml -f docker-compose.signing.yml up -d --wait api worker frontend opa presidio
```

On Windows use .venv/Scripts/python.exe; Linux/macOS use .venv/bin/python.
The key must be readable by uid 10001 in the container. On Linux set ownership
to that service identity and mode 0600; on Windows restrict host ACLs. Keys stay
in ignored secrets/. Use the same overlays for subsequent up/restart/run commands.

Presidio 2.2.366 uses spaCy 3.8.18 and en_core_web_sm 3.8.0. The model checksum
and licences are in docs/release/ and docs/third-party/. Only English and fixed
[REDACTED] replacement are supported. The small model and pattern recognizers
can miss PII or produce false positives; no universal PII or prompt-injection
coverage is claimed. Models and public-suffix data load locally without egress.

Enable each integration per tenant through Integration settings and check its
connection. URLs/tokens are deployment-only; tenant input cannot select hosts,
paths or commands. The standalone app works without optional services. Selecting
a disabled/unavailable service applies the policy's block/review error action.
The order is native, Presidio, OPA. OPA can block text previously sanitized because
it evaluates original PII presence. Never infer an allow from a failed control.

For key rotation, retain approved old Ed25519 public PEM keys in a mounted
directory and set TRUSTED_SIGNING_KEYS_DIR. Verification accepts trusted *.pub
keys and the configured active private key's public part. KMS is not implemented.

## Jobs, concurrency and privacy

PostgreSQL is authoritative. Redis carries JSON job pointers/rate counters.
Queued work is reconciled every 30 seconds. Running jobs older than ten minutes
become worker_interrupted and require manual retry. Cancellation is cooperative;
an external operation already completed cannot be undone. Retry creates a new
execution and validates current configuration. Presidio async input exists in
PostgreSQL while queued/running and is removed at terminal state. It cannot be
retried after removal. Encrypt storage and restrict database access. Synchronous
runtime events omit original and sanitized text.

The HTTP quota is 600 requests per identity per 60 seconds across its tenants;
other identities have independent quotas. Login has separate IP/account limits.
Each tenant can have ten outstanding jobs. PostgreSQL advisory locks serialize
quota/idempotency checks. Use Idempotency-Key on supported creation routes and
If-Match on versioned edits. HTTP 409 means reload/reconcile. SQLite is development-only.

## Verification and recovery

See docs/release/VERIFICATION.md and raw reports. scripts/release_checks.py runs
backend/frontend/browser gates. Browser tests require an isolated platform admin
in ignored tmp/release-browser-credentials.json (email/password). Never use
production credentials. Windows uses installed Edge Chromium; Linux CI installs
Playwright Chromium. Run benchmarks separately from browser tests.

scripts/verify_recovery.py controls only this project's services and synthetic
tenants. It removes one exact synthetic Redis pointer, injects an expired
synthetic lease, and verifies real reconciliation, RLS, cancellation, retry,
signatures, Redis persistence and HTTP rate limits. Do not run it during production
traffic. scripts/verify_postgres.py creates a separate temporary Windows cluster
for upgrade/downgrade/up and raw RLS tests; it never targets the live database.
CI fresh startup exercises real migrations.

Schedule encrypted pg_dump -Fc backups and point-in-time recovery as appropriate.
Back up signing material separately. Restore into a new isolated database and
verify evidence/audit/tenant records before switching traffic. Restart persistence
is tested; a full backup/restore disaster-recovery drill remains an operational
requirement. Retention/notification settings record intent/contact metadata only.

## Cloud and troubleshooting

docker-compose.production.yml is an untested VM/cloud template using Caddy.
It publishes 80/443 and requests certificates for DOMAIN. Configure TLS/CORS,
private data services, encryption, backups and alerts before use. Rebuild frontend
after changing NEXT_PUBLIC_API_URL. No cloud-readiness certification is claimed.

- Browser refresh clears memory-only sessions. 401 means expired/revoked session;
  403 means missing membership/role; foreign resource IDs return 404.
- 429 means a quota was exceeded. Do not run browser tests and benchmarks together.
  The benchmark uses a dedicated identity and paces outside timed HTTP requests.
- On Windows, cdxgen requires an absolute staging path without spaces: set
  UAG_SCAN_TMP_ROOT and UAG_NODE_EXECUTABLE in the API environment. Native Python
  reads process environment; only Compose reads .env automatically.
- Docker's former C: failure was resolved by the approved relocation to
  D:/DockerData/DockerDesktopWSL/disk/docker_data.vhdx. Do not reset Docker or
  delete unrelated services, images, networks or volumes to troubleshoot this app.
- Inspect only this app's Compose logs. Never copy credentials/prompts/private
  evidence to public issues. See docs/release/SECURITY_REVIEW.md for image findings.
