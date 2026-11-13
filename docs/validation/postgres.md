# PostgreSQL migration and isolation verification

On 2026-11-13, `python scripts/verify_postgres.py` passed 13 checks against an
actual PostgreSQL18.6 server on Windows. The [machine-readable result](postgres.json)
records commands, return codes, distribution hash and individual outcomes.

The script used EDB's portable Windows distribution, downloaded to ignored
`tmp/tools/pg18` on D:. Its SHA-256 matched the checksum confirmed by an EDB
contributor in [the official installer issue](https://github.com/EnterpriseDB/edb-installers/issues/746).
The [official PostgreSQL Windows page](https://www.postgresql.org/download/windows/)
links EDB's binary distribution. No installed PostgreSQL services or existing
data directories were changed. Only bin/lib/share were extracted; upstream
binaries and licences remain outside version control.

The test creates a unique cluster below `tmp/postgres-validation-*`, initializes
SCRAM authentication using a temporary random password file that is removed
immediately, and binds only127.0.0.1:15439. Credentials never appear in output.
The server was stopped successfully after the test. Synthetic cluster data
remains under ignored tmp for review; nothing is published or seeded into the app.

Verified behavior:

- Alembic upgrades successfully, then downgrades and upgrades again.
- records and audit_events have enabled and forced row-level security.
- The application test role is neither superuser nor BYPASSRLS.
- A connection without a tenant context reads zero tenant records.
- Raw SQL with tenantA context reads onlyA, cannot insertB records or audit
  events, cannot updateB rows, and cannot reassign anA record toB.
- Audit UPDATE and DELETE fail through the database trigger.
- Switching the explicit test context toB reads onlyB records.

RLS uses the transaction's application-set tenant context. The authenticated API
and trusted worker set that context; a party with arbitrary SQL execution as the
application role could set it themselves. Database superusers can bypass RLS and
alter triggers. The test does not claim protection from a compromised database
administrator or full PostgreSQL-backed API load validation.

The first harness run hit a Windows pipe-inheritance issue after pg_ctl had
successfully started its child server. That isolated server was stopped, and
output capture was changed to regular files before rerunning successfully. The
database implementation needed no change.
