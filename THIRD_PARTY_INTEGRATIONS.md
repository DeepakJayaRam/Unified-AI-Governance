# Third-party integration operations

Read [INTEGRATION_REGISTER.md](INTEGRATION_REGISTER.md) for all25 entries and all linked source records. Selection labels describe recommended mechanisms; executable availability is separately calculated from actual registered adapters and deployment configuration.

| Adapter | Actual implemented scope | Configuration / limits |
|---|---|---|
| cdxgen13.7.0 | Real CLI generates CycloneDX1.6 from staged npm manifest + v3 lockfile; raw BOM preserved | `timeout_seconds`1–120; operator Node>=24.15; scripts, local paths, external dependency installation denied |
| Compliance Trestle5.2.1 | Real package model validation of supported OSCAL JSON | JSON document input; no claim that arbitrary JSON/XML is OSCAL |
| in-toto statement/DSSE | Statement generation, Ed25519 signing and trusted-key verification | Private key via SIGNING_KEY_PATH; unsigned statement is not represented as a signature |
| OPA1.22.4 | HTTP policy evaluation of deployment-owned Rego | Operator OPA_URL; no tenant Rego or arbitrary endpoint; HTTP execution test requires service |
| Presidio | HTTP analyze/anonymize orchestration when deployed | Operator service URLs; language/entity limits; unconfigured by default and not claimed tested without service |

Evidence hashing and the native deterministic guardrail checks are original application functionality; they are never branded as upstream services. OSCAL Compass, official NIST resources and curated references are not executed. AI Verify, VerifyWise, NeMo, Llama Guard, Envoy and other unimplemented resources remain visibly deferred/restricted/reference entries according to their actual evidence. The OPA-Envoy plugin is researched under the same numbered entry as OPA, but proxy enforcement is not claimed from OPA alone.

No upstream trees are vendored. The npm discovery tool is installed in an isolated pinned tooling directory with reviewed overrides; retain its package licences and notices when distributing the built image. Python package dependencies and their transitive inventory are pinned in requirements.lock. Container images are pinned by inspected registry digest. Original app code is Apache-2.0; third-party code is not relicensed.

Upgrade procedure: verify official source/release/licence, update exact dependency/image pin, refresh source evidence, run isolated adapter negative tests and a genuine execution, preserve the command/result record, rerun vulnerability audits, update catalogue status and regenerate the readable register using scripts/build_register.py. If infrastructure is unavailable, record awaiting configuration instead of a successful execution.
