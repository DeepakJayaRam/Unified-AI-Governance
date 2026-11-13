# Third-party integration operations

The [25-entry register](INTEGRATION_REGISTER.md) distinguishes five tested
executable entries, five references, eleven deferred entries and four entries
restricted pending licence review. Presence in the catalogue never enables a tool.

| Adapter | Verified scope | Configuration |
|---|---|---|
| cdxgen 13.7.0 | Actual CLI creates CycloneDX 1.6 from npm manifest + v3 lockfile | Node 24.22.3 tested; minimum 24.15; timeout_seconds 1?120; no-space staging; no scripts/local/git dependencies |
| Compliance Trestle 5.2.1 | Actual OSCAL package models accept valid catalogues and reject invalid/unknown fields | JSON document; other model types are not individually fixture-tested |
| in-toto / DSSE | Application-owned Statement v1 and actual Ed25519 signing, trust verification and tampering rejection | SIGNING_KEY_PATH; optional TRUSTED_SIGNING_KEYS_DIR; no Cosign interoperability claim |
| OPA 1.22.4 | Real private HTTP allow/block/review, invalid compilation rejection and adapter failure handling | OPA_URL, optional OPA_TOKEN; pinned application Rego; no tenant Rego/URLs |
| Presidio 2.2.366 | Real analyzer/anonymizer HTTP, English model, replacement validation and prior-redaction preservation | PRESIDIO_ANALYZER_URL, PRESIDIO_ANONYMIZER_URL, optional corresponding _TOKEN variables |

Use docker-compose.presidio.yml for the optional private bridge. spaCy 3.8.18 and
en_core_web_sm 3.8.0 are pinned; the model wheel is SHA256-verified. Read the MIT
model licence and training-source notices in docs/third-party. English-only
recognizers have false negatives/positives and are not comprehensive protection.
URLs/tokens/keys are deployment-controlled; tenant forms accept only validated
adapter options. No model weights or upstream trees are vendored.

Cosign, Envoy and NeMo have no executable adapter in this release. OPA-Envoy is
deferred within OPA's numbered entry. VerifyWise VCEL requires separate written
commercial authorization. OpenComplAI AGPL obligations require review before
network service/source integration. The unlicensed EU toolkit cannot be copied;
Llama Guard requires exact model-specific licence review. ISO text is not included.

Native patterns, evidence hashes and governance checklists are original app
functionality. They are not branded as execution of reference tools. Optional
integration unavailability does not break unrelated native workflows; policies
that select unavailable controls explicitly block or request review.

Upgrade by verifying official source/release/licence, updating exact pins,
running genuine execution plus negative tests, retaining outputs, rerunning
audits, and updating docs/research JSON before scripts/build_register.py.
See docs/release/SECURITY_REVIEW.md for residual OS/OPA findings and expiry.
