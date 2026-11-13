# Deployment and operations

## Native development

Follow README.md. Use one API process with SQLite and `EXECUTION_MODE=local`; requests create durable job records before local background execution. After a development crash run `python -m uag.cli drain` to process queued jobs. A stale running job is marked interrupted, not automatically replayed. SQLite is not the supported shared production database or a substitute for PostgreSQL RLS.

Use separate environment values for test databases and live data. Set TEMP/TMP to a writable disk with sufficient space when the Windows system drive is constrained. cdxgen secure mode rejects spaces in the staging path; point operator-only UAG_SCAN_TMP_ROOT at an existing absolute no-space directory (tested: D:\uag-scan-temp). Health reports Not configured until this is satisfied. Existing development services must not be stopped or replaced merely to claim a port.

## Docker Compose

Prerequisites: working Docker engine, Compose 2.24.4+, 8 GB available RAM and adequate disk space. Image digests were inspected on 2026-11-13. Both dependency locks are checked in. Compose binds API/frontend to loopback ports 8100/3100; database, Redis and OPA have no host port bindings.

1. Copy `.env.example` to `.env` if one does not already exist. Set independent, random hexadecimal `POSTGRES_PASSWORD` and `APP_DB_PASSWORD` values. Avoid URL-reserved characters unless percent-encoding the database URL. Never commit `.env`.
2. Run `docker compose config --quiet` and `docker compose build`.
3. Run `docker compose up -d --wait api worker frontend opa`.
4. Run `docker compose exec api python -m uag.cli bootstrap --email admin@example.org --tenant "My organisation"`; enter a new password at the prompt.
5. Open `http://127.0.0.1:3100`, verify `/health` and create a real system/assessment. Review `docker compose logs api worker` without copying secrets into issues.

The migration service uses `uag_owner`; API and worker use `uag_app`, which must remain NOSUPERUSER/NOBYPASSRLS. `init-db.sh` creates this role only on a fresh database volume. Existing volumes need an explicitly reviewed role migration; changing `.env` does not rotate an existing PostgreSQL password. Never remove a volume to solve an authentication problem.

The API/worker run as uid10001 with a read-only root, bounded temporary space, CPU/memory/PID limits, dropped capabilities and no host source mounts. Redis is on an internal network and contains only JSON job pointers and rate counters. PostgreSQL remains the job source of truth. The worker reconciles queued work every 30 seconds. Integration execution is sequential per worker; scale deliberately and load-test before increasing concurrency.

## Signing and external model services

Generate private keys outside source control; inject `SIGNING_KEY_PATH` through a secret-mounted, read-only file readable only by uid10001 in the API. The worker's in-toto adapter creates unsigned statements and does not need the private key. Do not put key bytes in API configuration. The current local trust model verifies against the configured key; archive trusted public keys and plan key rotation before long-term attestation use. Automated managed-key/KMS signing is not implemented.

Optional service URLs are operator environment variables: `OPA_URL`, `PRESIDIO_ANALYZER_URL`, `PRESIDIO_ANONYMIZER_URL`. Use private service networking and authenticated ingress/service mesh where required. NeMo requires a separate compatible Python/model environment; Llama Guard requires model licence/access review and hardware-specific benchmarking. They are not part of the default synchronous pipeline.

## Cloud deployment

The application can run as separate API/frontend/worker services on a VM or container platform, with managed PostgreSQL and private Redis. Use a non-superuser application role and run migrations as a separate deployment job. Inject secrets through the cloud secret manager, restrict outbound scanner traffic, and use encrypted storage. No cloud account, DNS, public endpoint or external infrastructure is provisioned by this repository.

For a VM with DNS already directed to it, `docker-compose.production.yml` supplies a Caddy TLS ingress:

```text
DOMAIN=governance.example.org
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Set DOMAIN in the environment or `.env` before both commands. Review public ingress authorization before running: this variant opens 80/443 and obtains certificates. Browser API URL is a build-time Next.js value, so rebuild the frontend after changing it. Configure the correct CORS origin, production HSTS, backups, metrics and alert delivery before external clients. There is no public deployment performed in this project session.

## Backup and restore

Use scheduled encrypted `pg_dump -Fc` backups plus provider point-in-time recovery where available. Back up signing trust/key material using a separate access policy; losing the verification key can break historical validation. Store backups outside the application container and tenant-accessible paths. Redis can be recovered from PostgreSQL queued jobs; preserve it for rate counters and notifications, not governance records.

Restore into a **new isolated database**, run migration/version checks and verify tenant counts, evidence hashes, audit chain and sampled reports before switching traffic. Never test restore by overwriting a live database. Record recovery time and recovery point from an actual drill; none is assumed. The UI retention setting records policy intent only—automatic deletion/retention enforcement is not yet implemented.

## Troubleshooting and observed blockers

- Login after browser refresh is expected; memory-only sessions are intentional. Expired/revoked sessions return401. Missing tenant membership returns403 and foreign resource IDs return404.
- If API requests fail, match frontend NEXT_PUBLIC_API_URL, API CORS_ORIGINS and actual ports. Port3000 may belong to another application.
- An integration can be catalogued without being executable. Read its status, licence decision, config and actual test evidence. Health failure does not silently grant an allow decision.
- Node24.13.0 supports the frontend but is below the selected cdxgen transitive runtime requirement. Select the documented newer LTS for discovery.
- Docker initially ran `hello-world`, but later build/start attempts failed writing its internal metadata database with **read-only file system** while C: had very little free space. Compose configuration validation succeeded; container startup acceptance remains blocked until the Docker host is repaired. Do not remove existing images, volumes or unrelated files without owner approval.
- Starting the downloaded OPA server was rejected by automatic approval review with “blocked by policy”; its read-only version/policy checks were allowed. The HTTP service test remains unverified locally. Do not bypass this restriction.

See IMPLEMENTATION_STATUS.md and saved validation records for current pass/failure counts.

## Database verification evidence

An isolated native PostgreSQL18.6 cluster on127.0.0.1:15439 passed13 checks, including Alembic upgrade/down-up, application role restrictions, FORCE RLS, cross-tenant raw-SQL protection and append-only audit triggers. `scripts/verify_postgres.py` records the exact official binary source/hash and test result in `docs/validation/postgres.json`; it starts/stops only its freshly generated synthetic cluster. This verifies database behaviour independently of the still-blocked Docker engine. Never point this destructive test harness at a live cluster.
