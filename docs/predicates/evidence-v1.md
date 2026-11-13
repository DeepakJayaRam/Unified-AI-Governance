# Application evidence predicate v1

Identifier: `https://deepakjayaram.github.io/unified-ai-governance-security/predicates/evidence/v1`.
This is a stable identifier used in signed statements, not a claim that the website has been published.

The in-toto Statement v1 subject name is the tenant-scoped evidence record ID. Its sha256 digest is computed over the exact UTF-8 bytes accepted by the application. The predicate records tenant_id, evidence_id, actor_id, issued_at (UTC ISO8601) and media_type. The API supplies these fields from authenticated context, not from client assertions.

DSSE payload type is application/vnd.in-toto+json. Signing uses Ed25519 over DSSE pre-authentication encoding and the exact stored payload bytes. keyid is SHA256 of the raw public key. Verification uses deployment trust and binds the subject digest and evidence ID; it never trusts an envelope-supplied public key. A valid signature establishes origin/integrity within this trust model, not the factual accuracy or legal sufficiency of evidence.

The separate in-toto integration generates unsigned statements from user input and labels them signed=false. Such statements carry no authenticity claim.
