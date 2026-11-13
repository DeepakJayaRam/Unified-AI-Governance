# Security adapter validation ? v0.2

The current real-service tests are recorded in [release verification](release/VERIFICATION.md) and [backend output](release/backend-services.txt). All 55 backend tests passed with OPA, Presidio and cdxgen enabled. Separate loopback HTTP fault injection is explicitly distinguished from successful upstream-service execution.

OPA 1.22.4 executes the pinned governance policy over private HTTP. Missing classification requests review, unacceptable risk/unauthorized PII block, and allowed conditions permit processing. Invalid Rego compilation is rejected without replacing the loaded policy. Tenant callers cannot upload policy or choose URLs. OPA-Envoy and Envoy remain deferred.

The private Presidio bridge uses actual analyzer/anonymizer 2.2.366, spaCy 3.8.18 and en_core_web_sm 3.8.0 with a verified SHA256. English-only detection/redaction, malformed offsets, unsupported language, timeouts, failures and prior-redaction preservation are tested. No runtime downloads are required. Native?Presidio?OPA can execute synchronously when selected by a policy; asynchronous jobs are separately available. Synchronous events omit prompts, while async input is retained until terminal state and then removed.

Trestle 5.2.1 validates real OSCAL models. Catalogue positive/negative fixtures are covered; other supported model types are not individually fixture-tested. XML safety validation is not OSCAL XML schema validation. DSSE Ed25519 signatures bind exact evidence digest and identity; old trusted public keys can be retained through rotation using TRUSTED_SIGNING_KEYS_DIR. KMS, Cosign and public transparency logs are not implemented.

Read [security review](release/SECURITY_REVIEW.md) for residual image advisories, and LICENCE_AUDIT.md/THIRD_PARTY_NOTICES.md for model and upstream restrictions. Historical storage/startup blockers have been resolved; no Guardrail Sovereign services were modified.
