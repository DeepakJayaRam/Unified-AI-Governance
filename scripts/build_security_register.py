"""Build the reviewed security/evidence catalogue from inspected official sources."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SOURCES = BASE / "docs/research/sources"


def record(number, slug, layer, name, repo, classification, capabilities, installation,
           dependencies, api, sdk, cli, deployment, inputs, outputs, licence, maintenance,
           integration, risks, languages):
    source = json.loads((SOURCES / (repo.replace('/', '__') + '.json')).read_text(encoding='utf-8'))
    urls = [v['url'] for v in source['sources'].values()]
    return dict(id=slug, number=number, slug=slug, layer=layer, name=name,
                source_url='https://github.com/' + repo,
                official_source_url='https://github.com/' + repo,
                verified_project_name=name, sources=urls,
                inspected_revision=source.get('inspected_commit', 'community main README inspected'),
                latest_release=source.get('release_url', 'No independent umbrella release'),
                verified_on='2026-11-13', languages=languages,
                capabilities=capabilities, installation=installation, dependencies=dependencies,
                api=api, sdk=sdk, cli=cli, deployment=deployment,
                input_formats=inputs, output_formats=outputs,
                licence=licence, maintenance_status=maintenance,
                classification=classification, recommended_integration=integration,
                security_risks=risks,
                integration_test_status='RESEARCH_VERIFIED; execution not yet tested',
                verification_method='Official commit-pinned README, licence and listed source files; git ls-remote HEAD; GitHub latest release redirect and PyPI metadata when applicable. GitHub REST API unavailable due to shared anonymous rate limit.')


records = [
record(14, 'oscal-compass', 5, 'OSCAL Compass', 'oscal-compass/community', 'REFERENCE_RESOURCE',
       ['Umbrella community for Trestle, Agile Authoring and Compliance to Policy; separate project release cycles'],
       'No umbrella package. Select an independently licensed component; entry 15 covers Trestle.',
       ['Component-specific'], 'No umbrella API', 'Component-specific', 'No umbrella CLI',
       'Component-specific; community documentation is not a deployed service',
       ['Reference documentation'], ['Reference documentation'],
       'Community README identifies Apache-2.0; components require individual review. No upstream code bundled.',
       'Community README accessible and current; project-wide archive/maintenance metadata unavailable through rate-limited GitHub REST.',
       'Link reference material and use separately verified Compliance Trestle.',
       ['Do not treat umbrella documentation as executable or claim all components are installed.'],
       ['Markdown documentation; languages vary per component']),
record(15, 'compliance-trestle', 5, 'Compliance Trestle', 'oscal-compass/compliance-trestle', 'PACKAGE_DEPENDENCY',
       ['OSCAL Python object models', 'JSON/YAML validation and editing', 'Compliance authoring workflows', 'Detached JSON signing tools upstream'],
       'pip install compliance-trestle==5.2.1 in an isolated environment; Python >=3.11.',
       ['Pydantic 2', 'cryptography', 'ruamel.yaml', 'See pinned upstream pyproject.toml for full dependency list'],
       'Python API, not an upstream hosted REST service', 'trestle.oscal generated Pydantic models',
       'trestle (entry point trestle.cli:run)', 'Python package on Linux/macOS/Windows; CLI CI workflows',
       ['OSCAL JSON', 'OSCAL YAML', 'Authoring Markdown/CSV for specific workflows'],
       ['OSCAL JSON', 'OSCAL YAML', 'Authoring artefacts'],
       'Apache-2.0; preserve licence and notices when distributing package. No product-specific commercial prohibition identified.',
       'v5 actively developed; upstream states v4 maintenance through 2026-12-31 and v3 deprecated. v5 supports OSCAL 1.2.1; Python 3.14 listed.',
       'Use pinned Python object models for explicit catalogue/assessment format validation, preserve original document. XML support is not native.',
       ['Reject oversized/deep input and external references; validation proves schema conformance only, not control effectiveness.'],
       ['Python']),
record(16, 'cosign', 5, 'Sigstore Cosign', 'sigstore/cosign', 'CLI_INTEGRATION',
       ['Sign and verify blobs and OCI images', 'DSSE in-toto attestations', 'Keyless OIDC or private key/KMS signing'],
       'Install verified Cosign v3.1.4 official release binary for the target platform; validate release checksums/signatures before enabling.',
       ['Standalone Go binary; selected workflow may require OIDC/Fulcio/Rekor/TUF, OCI registry or KMS'],
       'No standalone Cosign hosted REST API; communicates with Sigstore and registries',
       'Go packages exist; CLI is recommended process boundary', 'cosign sign-blob / verify-blob / attest / verify-attestation',
       'Official release binaries and container packaging; isolated worker with read-only input and mounted secret/KMS access',
       ['Blob bytes', 'OCI image digest', 'Predicate JSON', 'Public key or expected certificate identity'],
       ['Signatures', 'Sigstore bundles', 'DSSE attestations', 'Verification results'],
       'Apache-2.0; preserve notices. Public transparency log terms and identity publication require deliberate operator choice.',
       'v3.1.4 latest release resolved; README says most recent release and last v2 release actively supported.',
       'Controlled CLI with explicit server-side signing configuration. Start with local key blob signing/verification; never trigger public transparency publication implicitly.',
       ['Private key exposure', 'Public and permanent transparency metadata', 'Trust-root freshness', 'Image tags are mutable; use digests'],
       ['Go']),
record(17, 'in-toto', 5, 'in-toto Attestation Framework', 'in-toto/attestation', 'NATIVE_ADAPTER',
       ['Versioned statement/envelope/predicate specification', 'Protobuf bindings for multiple languages'],
       'Specification does not require a service. Implement Statement v1 with a documented application predicate; optional language bindings are separate.',
       ['JSON serializer; cryptographic signer required separately for authenticity'],
       'Specification, no hosted API', 'Go/Python/Rust/Java bindings documented; Python package in-toto-attestation 0.9.3 inspected on PyPI',
       'No attestation CLI established by this specification repository', 'No standalone service required',
       ['Subject name and cryptographic digest', 'Predicate URI and predicate object'],
       ['https://in-toto.io/Statement/v1 JSON', 'Optional DSSE envelope when actually signed'],
       'Apache-2.0. Other predicate specifications may have separate licences.',
       'Specification latest release v1.2.0; inspected v1 statement/envelope documents. README warns tooling is still under development.',
       'Generate and structurally validate Statement v1 for evidence digest; mark unsigned until an actual signer signs and a verifier succeeds.',
       ['Unsigned statements do not establish identity or authenticity', 'Do not relabel custom predicates as SLSA provenance', 'Subject digest must bind exact bytes'],
       ['Protocol Buffers', 'Go', 'Python', 'Rust', 'Java', 'Markdown']),
record(18, 'aigrc', 6, 'aigrc', 'connectsmartconsulting/aigrc', 'DEFERRED',
       ['Adversarial prompt-injection and PII-leakage endpoint checks', 'JSON/SARIF/Markdown/HTML evidence reports', 'Offline mock target mode'],
       'Official README uses git clone then pip install -e .; package version 0.1.5 in pyproject. PyPI aigrc returned HTTP404; do not install a same-name unverified package.',
       ['Python >=3.10', 'typer', 'httpx', 'PyYAML', 'rich', 'Pydantic', 'Real provider credentials for openai target'],
       'Target openai://model-name supported by documented CLI; general target URL support not verified',
       'Python source package; no stable public SDK contract established', 'aigrc version; aigrc list; aigrc check prompt-injection / pii-leakage',
       'Python CLI in isolated worker; no production server established',
       ['Target URI and selected check'], ['JSON', 'SARIF 2.1.0', 'Markdown', 'HTML'],
       'MIT for repository code; proprietary methodology/services explicitly excluded from MIT code grant.',
       'v0.1.5; Python project classifier Alpha. Two live check types; future roadmap entries must not be represented as implemented.',
       'Defer execution until real authorized model endpoint and dependency-isolated pinned installation exist; allow report import. Offline examples are mocks.',
       ['Model prompts can contain adversarial content', 'Provider cost and data disclosure', 'Upstream mappings are claims, not legal compliance verification'],
       ['Python']),
record(19, 'opa', 6, 'Open Policy Agent + OPA-Envoy Plugin', 'open-policy-agent/opa', 'API_SERVICE',
       ['Rego policy evaluation over structured data', 'HTTP policy decision API', 'OPA-Envoy gRPC ext_authz enforcement'],
       'OPA v1.22.4 official binary/container; OPA-Envoy plugin v1.22.3-envoy is a distinct binary/image. Inspect compatibility before combining.',
       ['Standalone Go binary; Envoy and gRPC only for proxy enforcement'],
       'OPA REST POST /v1/data/{path} with {input:...}; GET /health. Plugin gRPC Envoy External Authorization API.',
       'Go library/Wasm options documented upstream; this app uses HTTP', 'opa eval; opa run --server',
       'Standalone service or OPA-Envoy sidecar; plugin README recommends policy bundles and health probes',
       ['Rego', 'JSON input/data', 'Policy bundles', 'Envoy ext_authz CheckRequest'],
       ['JSON decision results', 'Envoy authorization decisions', 'Metrics/decision logs if enabled'],
       'Apache-2.0 for both OPA and OPA-Envoy; preserve notices.',
       'Both repositories accessible with separate versioned releases. OPA1 Rego semantics require version-aware policies.',
       'Tenant-scoped input with server-managed policy namespace and explicit allow/block/review on errors. Test OPA itself separately from the untested Envoy proxy path.',
       ['Untrusted Rego can consume CPU or access network through built-ins; tenant-authored Rego is not accepted', 'Decision logs can disclose prompts', 'Unprotected data/policy APIs permit control-plane tampering'],
       ['Go', 'Rego']),
record(20, 'envoy', 6, 'Envoy Proxy', 'envoyproxy/envoy', 'CONTAINER_SERVICE',
       ['L7 proxy', 'External authorization filters', 'TLS and traffic telemetry'],
       'Pin official Envoy v1.40.2 image/release matching deployment platform; supply reviewed static or xDS configuration.',
       ['C++ binary; Linux/container runtime; TLS certificates; OPA-Envoy if selected'],
       'xDS and administrative API; ext_authz filter calls a separate authorization service',
       'Protocol buffer control-plane APIs, not Python governance SDK', 'envoy executable and config validation mode',
       'Official containers; local Docker daemon unavailable during initial inspection',
       ['YAML/JSON bootstrap configuration', 'HTTP/gRPC traffic', 'xDS protobuf'],
       ['Proxied traffic', 'Access logs and metrics', 'Authorization error responses'],
       'Apache-2.0; preserve notices and audit image dependencies.',
       'v1.40.2 latest release resolved; supported platform/security policy is upstream-specific.',
       'Optional separately deployed ingress with OPA-Envoy ext_authz; keep proxy admin port private and explicitly configure failure_mode_allow.',
       ['Exposed admin interface', 'Misconfigured TLS', 'Fail-open authorization', 'Logging sensitive bodies'],
       ['C++', 'Protocol Buffers', 'Python/build tooling']),
record(21, 'ai-verify', 6, 'AI Verify Toolkit', 'IMDA-BTG/aiverify', 'DEFERRED',
       ['Modular tests for supervised classification/regression systems', 'Tabular/image model evaluation', 'Test-engine plugin interfaces'],
       'Repository redirects to aiverify-foundation/aiverify, latest v2.2.2. Official engine install: pip install aiverify-test-engine; select and pin specific plugin separately.',
       ['Python test engine', 'Model/data dependencies including pandas/scikit-learn', 'Optional TensorFlow/PyTorch/GBM', 'Web app dependencies'],
       'Engine/plugin interfaces documented; stable external API endpoint contract not verified in this research',
       'aiverify_test_engine Python interfaces', 'Plugin-specific execution; no unified CLI assumed',
       'Separate evaluation worker/application requiring approved test data and model formats',
       ['CSV', 'Pandas pickle/joblib and model files are supported upstream but not safe for untrusted upload', 'Image datasets for selected plugins'],
       ['Plugin-specific metrics and reports'],
       'Apache-2.0 for repository; stock plugins/dependencies require additional review.',
       'v2.2.2 resolved at canonical Foundation repository; v2 engine modularization verified.',
       'Defer automatic execution until a specific plugin, model and dataset contract is selected. Import JSON evidence meanwhile; never deserialize user pickle/joblib on API host.',
       ['Arbitrary code execution from pickle/joblib/model plugins', 'Sensitive training/test data', 'Metrics do not prove bias-free or safe operation'],
       ['Python', 'TypeScript/JavaScript']),
record(22, 'verifywise', 6, 'VerifyWise', 'bluewave-labs/verifywise', 'BLOCKED_BY_LICENCE',
       ['AI governance platform with inventory/risk/evidence workflows', 'Framework workspaces and evaluation server'],
       'Do not install, redistribute or host for commercial client use in this application. Source redirects to verifywise-ai/verifywise.',
       ['React frontend', 'Node backend', 'PostgreSQL', 'Redis', 'Python >=3.12 EvalServer'],
       'Application backend exists; no API integrated because intended deployment is licence restricted',
       'No stable standalone SDK verified', 'npm/Docker installation scripts; not a scan CLI',
       'Upstream supports Docker/Kubernetes; not deployed by this project',
       ['Governance records and evaluation configuration'], ['Reports and governance records'],
       'CURRENT HEAD: VerifyWise Community & Evaluation License (VCEL) 1.0, October 2026, replaces BSL1.1 for new releases. Commercial organizational production use, hosting and redistribution require separate written authorization. Companies may evaluate for 60 days; qualifying personal/education/government/noncommercial uses have distinct grants. Existing releases retain their release licence. No commercial permission assumed.',
       'Latest redirect v2.6.7; current licence and licensing FAQ inspected at exact commit. Release-specific terms must be rechecked before any deployment.',
       'Catalogue reference with licence-restricted status; no executable adapter, bundled code or client hosting until documented commercial authorization.',
       ['Commercial licence restriction', 'Misleading old BSL1.1 assumptions', 'Multi-service sensitive data and credentials'],
       ['TypeScript/JavaScript', 'Python']),
record(23, 'presidio', 7, 'Presidio (originally Microsoft Presidio)', 'microsoft/presidio', 'API_SERVICE',
       ['Entity/PII detection with configured recognizers and NLP engine', 'Anonymization operators', 'Optional image redaction and model integrations'],
       'Source redirects to data-privacy-stack/presidio. pip install presidio-analyzer==2.2.366 presidio-anonymizer==2.2.366; configure NLP models separately. HTTP apps require server dependencies.',
       ['Python >=3.11,<3.15', 'spaCy/model packages for default NLP', 'Pydantic', 'Recognizer dependencies', 'Optional GPU for chosen models; deterministic recognizers can use CPU'],
       'Analyzer POST /analyze and GET /health; anonymizer POST /anonymize and GET /health verified in app.py',
       'presidio_analyzer.AnalyzerEngine and presidio_anonymizer.AnonymizerEngine',
       'No universal standalone scan CLI assumed', 'Separately deployed HTTP services or isolated packages; upstream Dockerfiles exist',
       ['Text, language and entity settings', 'Recognizer spans and anonymizer settings'],
       ['Entity type, start/end offsets and confidence', 'Anonymized text and items'],
       'MIT for Presidio code; NLP model licences and external service terms need separate review.',
       '2.2.366 on PyPI and latest release. Python3.14 supported by package metadata; default NLP model availability still environment-specific.',
       'Server-allowlisted analyzer/anonymizer HTTP endpoints; discard prompt text from logs. Distinguish recognizer coverage from comprehensive PII protection.',
       ['Text transfer to service', 'False negatives/positives', 'Model supply chain', 'PII in logs', 'Latency varies by model/text length and requires measurement'],
       ['Python']),
record(24, 'nemo-guardrails', 7, 'NVIDIA NeMo Guardrails', 'NVIDIA/NeMo-Guardrails', 'API_SERVICE',
       ['Input/dialog/retrieval/execution/output rails', 'Configurable Colang flows', 'Model-based safety and community integrations'],
       'Canonical repo NVIDIA-NeMo/Guardrails. Stable PyPI nemoguardrails==0.24.1 requires Python >=3.10,<3.14. Inspected HEAD is 0.25.0-rc1; do not install prerelease by default.',
       ['Model/provider access', 'onnxruntime/fastembed', 'Pydantic', 'Optional Presidio/transformers/server dependencies', 'GPU depends on selected model; remote LLMs add network latency'],
       'POST /v1/chat/completions with config_id and messages documented',
       'LLMRails, RailsConfig; generate and generate_async',
       'nemoguardrails chat / server / actions-server / evaluate', 'Separate Python3.12/3.13 service/container; incompatible with host Python3.14 stable package',
       ['Messages', 'Colang', 'YAML configuration', 'Python actions'], ['Guarded completions and evaluation outputs'],
       'Apache-2.0 code; model/provider and optional integration licences separate.',
       'Stable0.24.1; HEAD release candidate inspected. Do not conflate stable and HEAD compatibility.',
       'Allowlisted separately managed service; expensive model checks async/review path until measured. Do not accept arbitrary Python actions or configs from tenant input.',
       ['Configuration Python code execution', 'Model latency/cost', 'Prompt disclosure to provider', 'No rails configured means requests forwarded without guardrails'],
       ['Python', 'Colang']),
record(25, 'purple-llama', 7, 'Meta Purple Llama / Llama Guard', 'meta-llama/PurpleLlama', 'DEFERRED',
       ['Umbrella safety models and evaluations', 'Llama Guard content safety classification', 'Prompt Guard input attack classification', 'Code Shield and CyberSecEval are distinct components'],
       'Select exact model first, accept its current licence, download authorized weights and pin model revision. Transformers-based inference documented; no universal PurpleLlama service installer.',
       ['PyTorch/Transformers and model weights', 'Llama Guard3 variants 1B,8B,11B vision; quantized1B exists', 'RAM/VRAM/context limits depend on selected precision and serving runtime; no minimum hardware certified here'],
       'No single hosted PurpleLlama API; serving API depends on operator deployment',
       'Transformers inference examples; component-specific Python tooling', 'Component-specific eval CLIs; no umbrella CLI assumed',
       'Local/GPU inference or separately managed model endpoint; no weights downloaded and no commercial model terms accepted in this build',
       ['Conversations/text', 'Images for vision-specific model', 'Code for distinct Code Shield component'],
       ['Safety labels/categories or classifier scores', 'Component-specific evaluation results'],
       'Mixed licences: MIT evals/benchmarks/Code Shield; Llama models use model-specific Llama Community licences, not MIT. Current root LICENSE is Llama3.2 Community Agreement with attribution, acceptable-use and >700M monthly active user terms. README model/link inconsistencies mean recheck exact model repository licence before use.',
       'No umbrella release returned; exact HEAD recorded. README recommends PromptGuard2 over old PromptGuard. Exact model performance not tested.',
       'Defer model execution pending selected model, licence acceptance, hardware and benchmark. Keep heavyweight classifiers outside synchronous blocking until p95/p99 justify inclusion.',
       ['Model licence restrictions', 'Unsafe/incorrect classification', 'Prompt exposure', 'Large model memory/latency', 'Prompt Guard and content-safety Llama Guard have different purposes'],
       ['Python', 'Model artefacts'])
]

opa_plugin = json.loads((SOURCES / 'open-policy-agent__opa-envoy-plugin.json').read_text())
records[5]['secondary_sources'] = [{
    'url': 'https://github.com/open-policy-agent/opa-envoy-plugin',
    'inspected_revision': opa_plugin['inspected_commit'],
    'latest_release': opa_plugin['release_url'],
    'licence': 'Apache-2.0',
    'sources': [v['url'] for v in opa_plugin['sources'].values()]
}]

for item in records:
    if item['id'] == 'compliance-trestle':
        item['integration_test_status'] = 'EXECUTED: compliance-trestle5.2.1 accepted a valid OSCAL1.2.1 catalogue and rejected missing metadata/unknown fields via upstream models; raw JSON/hash preserved. Other supported model types are available but not individually fixture-tested.'
    elif item['id'] == 'in-toto':
        item['integration_test_status'] = 'EXECUTED: application-owned Statement v1 and Ed25519 DSSE signing/verification; tampered payload, digest, subject identity and unavailable key rejected. This is not a Cosign or Sigstore interoperability claim.'
    elif item['id'] == 'opa':
        item['integration_test_status'] = 'PARTIAL: official v1.22.4 Windows binary SHA256 verified; version and pinned Rego check exited0. HTTP adapter service test skipped. Docker image pulled but container startup failed (daemon filesystem read-only); background service launch rejected by automatic policy. OPA-Envoy untested.'
    elif item['id'] == 'presidio':
        item['integration_test_status'] = 'AWAITING_CONFIGURATION: HTTP adapter implemented from verified app.py contract; missing service/error-action and configuration rejection tests pass. No Presidio service/model installed or end-to-end PII coverage/latency measured.'
    elif item['id'] == 'verifywise':
        item['integration_test_status'] = 'BLOCKED_BY_LICENCE: source/licence inspected only; no install, deployment or execution.'

(BASE / 'docs/research/security.json').write_text(json.dumps(records, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
md = ['# Evidence, runtime and guardrail upstream verification', '',
      'Verified 2026-11-13 against official sources at recorded revisions. Classification describes the proposed technical boundary; execution status is separate. A verified interface is not an executed integration test.', '',
      'GitHub REST metadata was unavailable (anonymous rate limit). Official raw source files, git references, release redirects and PyPI metadata remained accessible. Archive status and full advisory history were not independently verified. No upstream source trees or model weights were incorporated.', '']
for r in records:
    md += [f"## {r['number']}. {r['name']}", '']
    for k,v in r.items():
        if k in ('id','slug','name','secondary_sources'): continue
        value = '; '.join(str(x) for x in v) if isinstance(v,list) else str(v)
        md += [f"- **{k.replace('_',' ').title()}:** {value}"]
    if 'secondary_sources' in r:
        md += ['- **OPA-Envoy secondary repository:** '+json.dumps(r['secondary_sources'][0])]
    md += ['']
(BASE / 'docs/research/security.md').write_text('\n'.join(md), encoding='utf-8')
print(f'Wrote {len(records)} records with verified sources.')
