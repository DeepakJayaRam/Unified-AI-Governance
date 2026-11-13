# Evidence, runtime and guardrail upstream verification

Verified 2026-11-13 against official sources at recorded revisions. Classification describes the proposed technical boundary; execution status is separate. A verified interface is not an executed integration test.

GitHub REST metadata was unavailable (anonymous rate limit). Official raw source files, git references, release redirects and PyPI metadata remained accessible. Archive status and full advisory history were not independently verified. No upstream source trees or model weights were incorporated.

## 14. OSCAL Compass

- **Number:** 14
- **Layer:** 5
- **Source Url:** https://github.com/oscal-compass/community
- **Official Source Url:** https://github.com/oscal-compass/community
- **Verified Project Name:** OSCAL Compass
- **Sources:** https://raw.githubusercontent.com/oscal-compass/community/main/README.md; https://raw.githubusercontent.com/oscal-compass/community/5998fc360fb91d14e730bd198ffc16906135b7ee/LICENSE
- **Inspected Revision:** 5998fc360fb91d14e730bd198ffc16906135b7ee
- **Latest Release:** No independent umbrella release
- **Verified On:** 2026-11-13
- **Languages:** Markdown documentation; languages vary per component
- **Capabilities:** Umbrella community for Trestle, Agile Authoring and Compliance to Policy; separate project release cycles
- **Installation:** No umbrella package. Select an independently licensed component; entry 15 covers Trestle.
- **Dependencies:** Component-specific
- **Api:** No umbrella API
- **Sdk:** Component-specific
- **Cli:** No umbrella CLI
- **Deployment:** Component-specific; community documentation is not a deployed service
- **Input Formats:** Reference documentation
- **Output Formats:** Reference documentation
- **Licence:** Community README identifies Apache-2.0; components require individual review. No upstream code bundled.
- **Maintenance Status:** Community README accessible and current; project-wide archive/maintenance metadata unavailable through rate-limited GitHub REST.
- **Classification:** REFERENCE_RESOURCE
- **Recommended Integration:** Link reference material and use separately verified Compliance Trestle.
- **Security Risks:** Do not treat umbrella documentation as executable or claim all components are installed.
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 15. Compliance Trestle

- **Number:** 15
- **Layer:** 5
- **Source Url:** https://github.com/oscal-compass/compliance-trestle
- **Official Source Url:** https://github.com/oscal-compass/compliance-trestle
- **Verified Project Name:** Compliance Trestle
- **Sources:** https://raw.githubusercontent.com/oscal-compass/compliance-trestle/4e350353586ce68b84a52988753b6fa45cdf34cb/README.md; https://raw.githubusercontent.com/oscal-compass/compliance-trestle/4e350353586ce68b84a52988753b6fa45cdf34cb/LICENSE; https://raw.githubusercontent.com/oscal-compass/compliance-trestle/4e350353586ce68b84a52988753b6fa45cdf34cb/pyproject.toml; https://raw.githubusercontent.com/oscal-compass/compliance-trestle/4e350353586ce68b84a52988753b6fa45cdf34cb/trestle/__init__.py; https://raw.githubusercontent.com/oscal-compass/compliance-trestle/4e350353586ce68b84a52988753b6fa45cdf34cb/trestle/oscal/catalog.py
- **Inspected Revision:** 4e350353586ce68b84a52988753b6fa45cdf34cb
- **Latest Release:** https://github.com/oscal-compass/compliance-trestle/releases/tag/v5.2.1
- **Verified On:** 2026-11-13
- **Languages:** Python
- **Capabilities:** OSCAL Python object models; JSON/YAML validation and editing; Compliance authoring workflows; Detached JSON signing tools upstream
- **Installation:** pip install compliance-trestle==5.2.1 in an isolated environment; Python >=3.11.
- **Dependencies:** Pydantic 2; cryptography; ruamel.yaml; See pinned upstream pyproject.toml for full dependency list
- **Api:** Python API, not an upstream hosted REST service
- **Sdk:** trestle.oscal generated Pydantic models
- **Cli:** trestle (entry point trestle.cli:run)
- **Deployment:** Python package on Linux/macOS/Windows; CLI CI workflows
- **Input Formats:** OSCAL JSON; OSCAL YAML; Authoring Markdown/CSV for specific workflows
- **Output Formats:** OSCAL JSON; OSCAL YAML; Authoring artefacts
- **Licence:** Apache-2.0; preserve licence and notices when distributing package. No product-specific commercial prohibition identified.
- **Maintenance Status:** v5 actively developed; upstream states v4 maintenance through 2026-12-31 and v3 deprecated. v5 supports OSCAL 1.2.1; Python 3.14 listed.
- **Classification:** PACKAGE_DEPENDENCY
- **Recommended Integration:** Use pinned Python object models for explicit catalogue/assessment format validation, preserve original document. XML support is not native.
- **Security Risks:** Reject oversized/deep input and external references; validation proves schema conformance only, not control effectiveness.
- **Integration Test Status:** EXECUTED: compliance-trestle5.2.1 accepted a valid OSCAL1.2.1 catalogue and rejected missing metadata/unknown fields via upstream models; raw JSON/hash preserved. Other supported model types are available but not individually fixture-tested.
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 16. Sigstore Cosign

- **Number:** 16
- **Layer:** 5
- **Source Url:** https://github.com/sigstore/cosign
- **Official Source Url:** https://github.com/sigstore/cosign
- **Verified Project Name:** Sigstore Cosign
- **Sources:** https://raw.githubusercontent.com/sigstore/cosign/6181e75677cc4719e845fa23d0ef8a936e883aa0/README.md; https://raw.githubusercontent.com/sigstore/cosign/6181e75677cc4719e845fa23d0ef8a936e883aa0/LICENSE
- **Inspected Revision:** 6181e75677cc4719e845fa23d0ef8a936e883aa0
- **Latest Release:** https://github.com/sigstore/cosign/releases/tag/v3.1.4
- **Verified On:** 2026-11-13
- **Languages:** Go
- **Capabilities:** Sign and verify blobs and OCI images; DSSE in-toto attestations; Keyless OIDC or private key/KMS signing
- **Installation:** Install verified Cosign v3.1.4 official release binary for the target platform; validate release checksums/signatures before enabling.
- **Dependencies:** Standalone Go binary; selected workflow may require OIDC/Fulcio/Rekor/TUF, OCI registry or KMS
- **Api:** No standalone Cosign hosted REST API; communicates with Sigstore and registries
- **Sdk:** Go packages exist; CLI is recommended process boundary
- **Cli:** cosign sign-blob / verify-blob / attest / verify-attestation
- **Deployment:** Official release binaries and container packaging; isolated worker with read-only input and mounted secret/KMS access
- **Input Formats:** Blob bytes; OCI image digest; Predicate JSON; Public key or expected certificate identity
- **Output Formats:** Signatures; Sigstore bundles; DSSE attestations; Verification results
- **Licence:** Apache-2.0; preserve notices. Public transparency log terms and identity publication require deliberate operator choice.
- **Maintenance Status:** v3.1.4 latest release resolved; README says most recent release and last v2 release actively supported.
- **Classification:** CLI_INTEGRATION
- **Recommended Integration:** Controlled CLI with explicit server-side signing configuration. Start with local key blob signing/verification; never trigger public transparency publication implicitly.
- **Security Risks:** Private key exposure; Public and permanent transparency metadata; Trust-root freshness; Image tags are mutable; use digests
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 17. in-toto Attestation Framework

- **Number:** 17
- **Layer:** 5
- **Source Url:** https://github.com/in-toto/attestation
- **Official Source Url:** https://github.com/in-toto/attestation
- **Verified Project Name:** in-toto Attestation Framework
- **Sources:** https://raw.githubusercontent.com/in-toto/attestation/50bf01716982189898823e90586075f37cd9bb7d/README.md; https://raw.githubusercontent.com/in-toto/attestation/50bf01716982189898823e90586075f37cd9bb7d/LICENSE; https://raw.githubusercontent.com/in-toto/attestation/50bf01716982189898823e90586075f37cd9bb7d/package.json; https://raw.githubusercontent.com/in-toto/attestation/50bf01716982189898823e90586075f37cd9bb7d/spec/v1/statement.md; https://raw.githubusercontent.com/in-toto/attestation/50bf01716982189898823e90586075f37cd9bb7d/spec/v1/envelope.md
- **Inspected Revision:** 50bf01716982189898823e90586075f37cd9bb7d
- **Latest Release:** https://github.com/in-toto/attestation/releases/tag/v1.2.0
- **Verified On:** 2026-11-13
- **Languages:** Protocol Buffers; Go; Python; Rust; Java; Markdown
- **Capabilities:** Versioned statement/envelope/predicate specification; Protobuf bindings for multiple languages
- **Installation:** Specification does not require a service. Implement Statement v1 with a documented application predicate; optional language bindings are separate.
- **Dependencies:** JSON serializer; cryptographic signer required separately for authenticity
- **Api:** Specification, no hosted API
- **Sdk:** Go/Python/Rust/Java bindings documented; Python package in-toto-attestation 0.9.3 inspected on PyPI
- **Cli:** No attestation CLI established by this specification repository
- **Deployment:** No standalone service required
- **Input Formats:** Subject name and cryptographic digest; Predicate URI and predicate object
- **Output Formats:** https://in-toto.io/Statement/v1 JSON; Optional DSSE envelope when actually signed
- **Licence:** Apache-2.0. Other predicate specifications may have separate licences.
- **Maintenance Status:** Specification latest release v1.2.0; inspected v1 statement/envelope documents. README warns tooling is still under development.
- **Classification:** NATIVE_ADAPTER
- **Recommended Integration:** Generate and structurally validate Statement v1 for evidence digest; mark unsigned until an actual signer signs and a verifier succeeds.
- **Security Risks:** Unsigned statements do not establish identity or authenticity; Do not relabel custom predicates as SLSA provenance; Subject digest must bind exact bytes
- **Integration Test Status:** EXECUTED: application-owned Statement v1 and Ed25519 DSSE signing/verification; tampered payload, digest, subject identity and unavailable key rejected. This is not a Cosign or Sigstore interoperability claim.
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 18. aigrc

- **Number:** 18
- **Layer:** 6
- **Source Url:** https://github.com/connectsmartconsulting/aigrc
- **Official Source Url:** https://github.com/connectsmartconsulting/aigrc
- **Verified Project Name:** aigrc
- **Sources:** https://raw.githubusercontent.com/connectsmartconsulting/aigrc/27846f1e878e6df6845fe0c416bab668b6d941c1/README.md; https://raw.githubusercontent.com/connectsmartconsulting/aigrc/27846f1e878e6df6845fe0c416bab668b6d941c1/LICENSE; https://raw.githubusercontent.com/connectsmartconsulting/aigrc/27846f1e878e6df6845fe0c416bab668b6d941c1/pyproject.toml
- **Inspected Revision:** 27846f1e878e6df6845fe0c416bab668b6d941c1
- **Latest Release:** https://github.com/connectsmartconsulting/aigrc/releases/tag/v0.1.5
- **Verified On:** 2026-11-13
- **Languages:** Python
- **Capabilities:** Adversarial prompt-injection and PII-leakage endpoint checks; JSON/SARIF/Markdown/HTML evidence reports; Offline mock target mode
- **Installation:** Official README uses git clone then pip install -e .; package version 0.1.5 in pyproject. PyPI aigrc returned HTTP404; do not install a same-name unverified package.
- **Dependencies:** Python >=3.10; typer; httpx; PyYAML; rich; Pydantic; Real provider credentials for openai target
- **Api:** Target openai://model-name supported by documented CLI; general target URL support not verified
- **Sdk:** Python source package; no stable public SDK contract established
- **Cli:** aigrc version; aigrc list; aigrc check prompt-injection / pii-leakage
- **Deployment:** Python CLI in isolated worker; no production server established
- **Input Formats:** Target URI and selected check
- **Output Formats:** JSON; SARIF 2.1.0; Markdown; HTML
- **Licence:** MIT for repository code; proprietary methodology/services explicitly excluded from MIT code grant.
- **Maintenance Status:** v0.1.5; Python project classifier Alpha. Two live check types; future roadmap entries must not be represented as implemented.
- **Classification:** DEFERRED
- **Recommended Integration:** Defer execution until real authorized model endpoint and dependency-isolated pinned installation exist; allow report import. Offline examples are mocks.
- **Security Risks:** Model prompts can contain adversarial content; Provider cost and data disclosure; Upstream mappings are claims, not legal compliance verification
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 19. Open Policy Agent + OPA-Envoy Plugin

- **Number:** 19
- **Layer:** 6
- **Source Url:** https://github.com/open-policy-agent/opa
- **Official Source Url:** https://github.com/open-policy-agent/opa
- **Verified Project Name:** Open Policy Agent + OPA-Envoy Plugin
- **Sources:** https://raw.githubusercontent.com/open-policy-agent/opa/c53079d691070ea0a14cdcfee829ec7055ae601f/README.md; https://raw.githubusercontent.com/open-policy-agent/opa/c53079d691070ea0a14cdcfee829ec7055ae601f/LICENSE; https://raw.githubusercontent.com/open-policy-agent/opa/c53079d691070ea0a14cdcfee829ec7055ae601f/docs/docs/rest-api.md; https://raw.githubusercontent.com/open-policy-agent/opa/c53079d691070ea0a14cdcfee829ec7055ae601f/docs/docs/policy-language.md
- **Inspected Revision:** c53079d691070ea0a14cdcfee829ec7055ae601f
- **Latest Release:** https://github.com/open-policy-agent/opa/releases/tag/v1.22.4
- **Verified On:** 2026-11-13
- **Languages:** Go; Rego
- **Capabilities:** Rego policy evaluation over structured data; HTTP policy decision API; OPA-Envoy gRPC ext_authz enforcement
- **Installation:** OPA v1.22.4 official binary/container; OPA-Envoy plugin v1.22.3-envoy is a distinct binary/image. Inspect compatibility before combining.
- **Dependencies:** Standalone Go binary; Envoy and gRPC only for proxy enforcement
- **Api:** OPA REST POST /v1/data/{path} with {input:...}; GET /health. Plugin gRPC Envoy External Authorization API.
- **Sdk:** Go library/Wasm options documented upstream; this app uses HTTP
- **Cli:** opa eval; opa run --server
- **Deployment:** Standalone service or OPA-Envoy sidecar; plugin README recommends policy bundles and health probes
- **Input Formats:** Rego; JSON input/data; Policy bundles; Envoy ext_authz CheckRequest
- **Output Formats:** JSON decision results; Envoy authorization decisions; Metrics/decision logs if enabled
- **Licence:** Apache-2.0 for both OPA and OPA-Envoy; preserve notices.
- **Maintenance Status:** Both repositories accessible with separate versioned releases. OPA1 Rego semantics require version-aware policies.
- **Classification:** API_SERVICE
- **Recommended Integration:** Tenant-scoped input with server-managed policy namespace and explicit allow/block/review on errors. Test OPA itself separately from the untested Envoy proxy path.
- **Security Risks:** Untrusted Rego can consume CPU or access network through built-ins; tenant-authored Rego is not accepted; Decision logs can disclose prompts; Unprotected data/policy APIs permit control-plane tampering
- **Integration Test Status:** PARTIAL: official v1.22.4 Windows binary SHA256 verified; version and pinned Rego check exited0. HTTP adapter service test skipped. Docker image pulled but container startup failed (daemon filesystem read-only); background service launch rejected by automatic policy. OPA-Envoy untested.
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.
- **OPA-Envoy secondary repository:** {"url": "https://github.com/open-policy-agent/opa-envoy-plugin", "inspected_revision": "f60542a9b76754b78fe8d373160dc1a3044376ec", "latest_release": "https://github.com/open-policy-agent/opa-envoy-plugin/releases/tag/v1.22.3-envoy", "licence": "Apache-2.0", "sources": ["https://raw.githubusercontent.com/open-policy-agent/opa-envoy-plugin/f60542a9b76754b78fe8d373160dc1a3044376ec/README.md", "https://raw.githubusercontent.com/open-policy-agent/opa-envoy-plugin/f60542a9b76754b78fe8d373160dc1a3044376ec/LICENSE"]}

## 20. Envoy Proxy

- **Number:** 20
- **Layer:** 6
- **Source Url:** https://github.com/envoyproxy/envoy
- **Official Source Url:** https://github.com/envoyproxy/envoy
- **Verified Project Name:** Envoy Proxy
- **Sources:** https://raw.githubusercontent.com/envoyproxy/envoy/35005437106e90105a9d8b76fdfa9e7152ed4287/README.md; https://raw.githubusercontent.com/envoyproxy/envoy/35005437106e90105a9d8b76fdfa9e7152ed4287/LICENSE
- **Inspected Revision:** 35005437106e90105a9d8b76fdfa9e7152ed4287
- **Latest Release:** https://github.com/envoyproxy/envoy/releases/tag/v1.40.2
- **Verified On:** 2026-11-13
- **Languages:** C++; Protocol Buffers; Python/build tooling
- **Capabilities:** L7 proxy; External authorization filters; TLS and traffic telemetry
- **Installation:** Pin official Envoy v1.40.2 image/release matching deployment platform; supply reviewed static or xDS configuration.
- **Dependencies:** C++ binary; Linux/container runtime; TLS certificates; OPA-Envoy if selected
- **Api:** xDS and administrative API; ext_authz filter calls a separate authorization service
- **Sdk:** Protocol buffer control-plane APIs, not Python governance SDK
- **Cli:** envoy executable and config validation mode
- **Deployment:** Official containers; local Docker daemon unavailable during initial inspection
- **Input Formats:** YAML/JSON bootstrap configuration; HTTP/gRPC traffic; xDS protobuf
- **Output Formats:** Proxied traffic; Access logs and metrics; Authorization error responses
- **Licence:** Apache-2.0; preserve notices and audit image dependencies.
- **Maintenance Status:** v1.40.2 latest release resolved; supported platform/security policy is upstream-specific.
- **Classification:** CONTAINER_SERVICE
- **Recommended Integration:** Optional separately deployed ingress with OPA-Envoy ext_authz; keep proxy admin port private and explicitly configure failure_mode_allow.
- **Security Risks:** Exposed admin interface; Misconfigured TLS; Fail-open authorization; Logging sensitive bodies
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 21. AI Verify Toolkit

- **Number:** 21
- **Layer:** 6
- **Source Url:** https://github.com/IMDA-BTG/aiverify
- **Official Source Url:** https://github.com/IMDA-BTG/aiverify
- **Verified Project Name:** AI Verify Toolkit
- **Sources:** https://raw.githubusercontent.com/IMDA-BTG/aiverify/3f58c3eb6cdff0c02617b4e1910ca30dad080f12/README.md; https://raw.githubusercontent.com/IMDA-BTG/aiverify/3f58c3eb6cdff0c02617b4e1910ca30dad080f12/LICENSE; https://raw.githubusercontent.com/IMDA-BTG/aiverify/3f58c3eb6cdff0c02617b4e1910ca30dad080f12/package.json; https://raw.githubusercontent.com/IMDA-BTG/aiverify/3f58c3eb6cdff0c02617b4e1910ca30dad080f12/aiverify-test-engine/README.md
- **Inspected Revision:** 3f58c3eb6cdff0c02617b4e1910ca30dad080f12
- **Latest Release:** https://github.com/aiverify-foundation/aiverify/releases/tag/v2.2.2
- **Verified On:** 2026-11-13
- **Languages:** Python; TypeScript/JavaScript
- **Capabilities:** Modular tests for supervised classification/regression systems; Tabular/image model evaluation; Test-engine plugin interfaces
- **Installation:** Repository redirects to aiverify-foundation/aiverify, latest v2.2.2. Official engine install: pip install aiverify-test-engine; select and pin specific plugin separately.
- **Dependencies:** Python test engine; Model/data dependencies including pandas/scikit-learn; Optional TensorFlow/PyTorch/GBM; Web app dependencies
- **Api:** Engine/plugin interfaces documented; stable external API endpoint contract not verified in this research
- **Sdk:** aiverify_test_engine Python interfaces
- **Cli:** Plugin-specific execution; no unified CLI assumed
- **Deployment:** Separate evaluation worker/application requiring approved test data and model formats
- **Input Formats:** CSV; Pandas pickle/joblib and model files are supported upstream but not safe for untrusted upload; Image datasets for selected plugins
- **Output Formats:** Plugin-specific metrics and reports
- **Licence:** Apache-2.0 for repository; stock plugins/dependencies require additional review.
- **Maintenance Status:** v2.2.2 resolved at canonical Foundation repository; v2 engine modularization verified.
- **Classification:** DEFERRED
- **Recommended Integration:** Defer automatic execution until a specific plugin, model and dataset contract is selected. Import JSON evidence meanwhile; never deserialize user pickle/joblib on API host.
- **Security Risks:** Arbitrary code execution from pickle/joblib/model plugins; Sensitive training/test data; Metrics do not prove bias-free or safe operation
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 22. VerifyWise

- **Number:** 22
- **Layer:** 6
- **Source Url:** https://github.com/bluewave-labs/verifywise
- **Official Source Url:** https://github.com/bluewave-labs/verifywise
- **Verified Project Name:** VerifyWise
- **Sources:** https://raw.githubusercontent.com/bluewave-labs/verifywise/5f2e6c36dc8fbf03fec8277039d633bc62a750ee/README.md; https://raw.githubusercontent.com/bluewave-labs/verifywise/5f2e6c36dc8fbf03fec8277039d633bc62a750ee/LICENSE.md; https://raw.githubusercontent.com/bluewave-labs/verifywise/5f2e6c36dc8fbf03fec8277039d633bc62a750ee/package.json; https://raw.githubusercontent.com/bluewave-labs/verifywise/5f2e6c36dc8fbf03fec8277039d633bc62a750ee/LICENSING-FAQ.md
- **Inspected Revision:** 5f2e6c36dc8fbf03fec8277039d633bc62a750ee
- **Latest Release:** https://github.com/verifywise-ai/verifywise/releases/tag/v2.6.7
- **Verified On:** 2026-11-13
- **Languages:** TypeScript/JavaScript; Python
- **Capabilities:** AI governance platform with inventory/risk/evidence workflows; Framework workspaces and evaluation server
- **Installation:** Do not install, redistribute or host for commercial client use in this application. Source redirects to verifywise-ai/verifywise.
- **Dependencies:** React frontend; Node backend; PostgreSQL; Redis; Python >=3.12 EvalServer
- **Api:** Application backend exists; no API integrated because intended deployment is licence restricted
- **Sdk:** No stable standalone SDK verified
- **Cli:** npm/Docker installation scripts; not a scan CLI
- **Deployment:** Upstream supports Docker/Kubernetes; not deployed by this project
- **Input Formats:** Governance records and evaluation configuration
- **Output Formats:** Reports and governance records
- **Licence:** CURRENT HEAD: VerifyWise Community & Evaluation License (VCEL) 1.0, October 2026, replaces BSL1.1 for new releases. Commercial organizational production use, hosting and redistribution require separate written authorization. Companies may evaluate for 60 days; qualifying personal/education/government/noncommercial uses have distinct grants. Existing releases retain their release licence. No commercial permission assumed.
- **Maintenance Status:** Latest redirect v2.6.7; current licence and licensing FAQ inspected at exact commit. Release-specific terms must be rechecked before any deployment.
- **Classification:** BLOCKED_BY_LICENCE
- **Recommended Integration:** Catalogue reference with licence-restricted status; no executable adapter, bundled code or client hosting until documented commercial authorization.
- **Security Risks:** Commercial licence restriction; Misleading old BSL1.1 assumptions; Multi-service sensitive data and credentials
- **Integration Test Status:** BLOCKED_BY_LICENCE: source/licence inspected only; no install, deployment or execution.
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 23. Presidio (originally Microsoft Presidio)

- **Number:** 23
- **Layer:** 7
- **Source Url:** https://github.com/microsoft/presidio
- **Official Source Url:** https://github.com/microsoft/presidio
- **Verified Project Name:** Presidio (originally Microsoft Presidio)
- **Sources:** https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/LICENSE; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/pyproject.toml; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/README.MD; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/presidio-analyzer/pyproject.toml; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/presidio-analyzer/app.py; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/presidio-anonymizer/app.py; https://raw.githubusercontent.com/microsoft/presidio/aa77b9f98f2c3a2de0f16974e7b540702938707e/docker-compose.yml
- **Inspected Revision:** aa77b9f98f2c3a2de0f16974e7b540702938707e
- **Latest Release:** https://github.com/data-privacy-stack/presidio/releases/tag/2.2.366
- **Verified On:** 2026-11-13
- **Languages:** Python
- **Capabilities:** Entity/PII detection with configured recognizers and NLP engine; Anonymization operators; Optional image redaction and model integrations
- **Installation:** Source redirects to data-privacy-stack/presidio. pip install presidio-analyzer==2.2.366 presidio-anonymizer==2.2.366; configure NLP models separately. HTTP apps require server dependencies.
- **Dependencies:** Python >=3.11,<3.15; spaCy/model packages for default NLP; Pydantic; Recognizer dependencies; Optional GPU for chosen models; deterministic recognizers can use CPU
- **Api:** Analyzer POST /analyze and GET /health; anonymizer POST /anonymize and GET /health verified in app.py
- **Sdk:** presidio_analyzer.AnalyzerEngine and presidio_anonymizer.AnonymizerEngine
- **Cli:** No universal standalone scan CLI assumed
- **Deployment:** Separately deployed HTTP services or isolated packages; upstream Dockerfiles exist
- **Input Formats:** Text, language and entity settings; Recognizer spans and anonymizer settings
- **Output Formats:** Entity type, start/end offsets and confidence; Anonymized text and items
- **Licence:** MIT for Presidio code; NLP model licences and external service terms need separate review.
- **Maintenance Status:** 2.2.366 on PyPI and latest release. Python3.14 supported by package metadata; default NLP model availability still environment-specific.
- **Classification:** API_SERVICE
- **Recommended Integration:** Server-allowlisted analyzer/anonymizer HTTP endpoints; discard prompt text from logs. Distinguish recognizer coverage from comprehensive PII protection.
- **Security Risks:** Text transfer to service; False negatives/positives; Model supply chain; PII in logs; Latency varies by model/text length and requires measurement
- **Integration Test Status:** AWAITING_CONFIGURATION: HTTP adapter implemented from verified app.py contract; missing service/error-action and configuration rejection tests pass. No Presidio service/model installed or end-to-end PII coverage/latency measured.
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 24. NVIDIA NeMo Guardrails

- **Number:** 24
- **Layer:** 7
- **Source Url:** https://github.com/NVIDIA/NeMo-Guardrails
- **Official Source Url:** https://github.com/NVIDIA/NeMo-Guardrails
- **Verified Project Name:** NVIDIA NeMo Guardrails
- **Sources:** https://raw.githubusercontent.com/NVIDIA/NeMo-Guardrails/200cd26fa771b4205c2339a1a13a1d7e2623e756/README.md; https://raw.githubusercontent.com/NVIDIA/NeMo-Guardrails/200cd26fa771b4205c2339a1a13a1d7e2623e756/LICENSE.md; https://raw.githubusercontent.com/NVIDIA/NeMo-Guardrails/200cd26fa771b4205c2339a1a13a1d7e2623e756/pyproject.toml; https://raw.githubusercontent.com/NVIDIA/NeMo-Guardrails/200cd26fa771b4205c2339a1a13a1d7e2623e756/package.json
- **Inspected Revision:** 200cd26fa771b4205c2339a1a13a1d7e2623e756
- **Latest Release:** https://github.com/NVIDIA-NeMo/Guardrails/releases/tag/v0.24.1
- **Verified On:** 2026-11-13
- **Languages:** Python; Colang
- **Capabilities:** Input/dialog/retrieval/execution/output rails; Configurable Colang flows; Model-based safety and community integrations
- **Installation:** Canonical repo NVIDIA-NeMo/Guardrails. Stable PyPI nemoguardrails==0.24.1 requires Python >=3.10,<3.14. Inspected HEAD is 0.25.0-rc1; do not install prerelease by default.
- **Dependencies:** Model/provider access; onnxruntime/fastembed; Pydantic; Optional Presidio/transformers/server dependencies; GPU depends on selected model; remote LLMs add network latency
- **Api:** POST /v1/chat/completions with config_id and messages documented
- **Sdk:** LLMRails, RailsConfig; generate and generate_async
- **Cli:** nemoguardrails chat / server / actions-server / evaluate
- **Deployment:** Separate Python3.12/3.13 service/container; incompatible with host Python3.14 stable package
- **Input Formats:** Messages; Colang; YAML configuration; Python actions
- **Output Formats:** Guarded completions and evaluation outputs
- **Licence:** Apache-2.0 code; model/provider and optional integration licences separate.
- **Maintenance Status:** Stable0.24.1; HEAD release candidate inspected. Do not conflate stable and HEAD compatibility.
- **Classification:** API_SERVICE
- **Recommended Integration:** Allowlisted separately managed service; expensive model checks async/review path until measured. Do not accept arbitrary Python actions or configs from tenant input.
- **Security Risks:** Configuration Python code execution; Model latency/cost; Prompt disclosure to provider; No rails configured means requests forwarded without guardrails
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.

## 25. Meta Purple Llama / Llama Guard

- **Number:** 25
- **Layer:** 7
- **Source Url:** https://github.com/meta-llama/PurpleLlama
- **Official Source Url:** https://github.com/meta-llama/PurpleLlama
- **Verified Project Name:** Meta Purple Llama / Llama Guard
- **Sources:** https://raw.githubusercontent.com/meta-llama/PurpleLlama/7e163b68c0af2ced1fae19ddbd471a8c36341519/README.md; https://raw.githubusercontent.com/meta-llama/PurpleLlama/7e163b68c0af2ced1fae19ddbd471a8c36341519/LICENSE; https://raw.githubusercontent.com/meta-llama/PurpleLlama/7e163b68c0af2ced1fae19ddbd471a8c36341519/Llama-Guard3/README.md; https://raw.githubusercontent.com/meta-llama/PurpleLlama/7e163b68c0af2ced1fae19ddbd471a8c36341519/Prompt-Guard/README.md
- **Inspected Revision:** 7e163b68c0af2ced1fae19ddbd471a8c36341519
- **Latest Release:** https://github.com/meta-llama/PurpleLlama/releases
- **Verified On:** 2026-11-13
- **Languages:** Python; Model artefacts
- **Capabilities:** Umbrella safety models and evaluations; Llama Guard content safety classification; Prompt Guard input attack classification; Code Shield and CyberSecEval are distinct components
- **Installation:** Select exact model first, accept its current licence, download authorized weights and pin model revision. Transformers-based inference documented; no universal PurpleLlama service installer.
- **Dependencies:** PyTorch/Transformers and model weights; Llama Guard3 variants 1B,8B,11B vision; quantized1B exists; RAM/VRAM/context limits depend on selected precision and serving runtime; no minimum hardware certified here
- **Api:** No single hosted PurpleLlama API; serving API depends on operator deployment
- **Sdk:** Transformers inference examples; component-specific Python tooling
- **Cli:** Component-specific eval CLIs; no umbrella CLI assumed
- **Deployment:** Local/GPU inference or separately managed model endpoint; no weights downloaded and no commercial model terms accepted in this build
- **Input Formats:** Conversations/text; Images for vision-specific model; Code for distinct Code Shield component
- **Output Formats:** Safety labels/categories or classifier scores; Component-specific evaluation results
- **Licence:** Mixed licences: MIT evals/benchmarks/Code Shield; Llama models use model-specific Llama Community licences, not MIT. Current root LICENSE is Llama3.2 Community Agreement with attribution, acceptable-use and >700M monthly active user terms. README model/link inconsistencies mean recheck exact model repository licence before use.
- **Maintenance Status:** No umbrella release returned; exact HEAD recorded. README recommends PromptGuard2 over old PromptGuard. Exact model performance not tested.
- **Classification:** DEFERRED
- **Recommended Integration:** Defer model execution pending selected model, licence acceptance, hardware and benchmark. Keep heavyweight classifiers outside synchronous blocking until p95/p99 justify inclusion.
- **Security Risks:** Model licence restrictions; Unsafe/incorrect classification; Prompt exposure; Large model memory/latency; Prompt Guard and content-safety Llama Guard have different purposes
- **Integration Test Status:** RESEARCH_VERIFIED; execution not yet tested
- **Verification Method:** Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.
