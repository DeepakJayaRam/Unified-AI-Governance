# Evidence and runtime integration validation

Inspected and tested on 2026-11-13, Windows amd64, Python3.14.2. The upstream register is `docs/research/security.json`; official source URLs, commits, file hashes and release redirects are retained in `docs/research/sources/`. Downloaded inspection content was removed from the retained records; upstream source trees and model weights are not bundled.

## Executed validations

| Component | Actual command or operation | Observed result |
| --- | --- | --- |
| Compliance Trestle | `.venv/Scripts/python.exe -m pip install compliance-trestle==5.2.1` | Official PyPI wheel installed with dependencies; version5.2.1 verified by importlib metadata. |
| OSCAL | `TrestleAdapter.execute` via `pytest tests/test_security_adapters.py` | Upstream Trestle models accepted an application-owned OSCAL1.2.1 catalogue, rejected missing metadata and unknown fields; original JSON and SHA256 retained. |
| in-toto/DSSE | `pytest tests/test_security_adapters.py` | Actual Ed25519 signing and verification; tampering, wrong subject digest/name and unavailable key rejected. Local temporary test key only. |
| Evidence API | Same pytest invocation | Create, exact-byte hash, download, sign, verify, ZIP export and cross-tenant denial exercised against actual FastAPI/SQLAlchemy application using test SQLite. XML external entities and non-finite JSON rejected. |
| Bounded subprocess | Same pytest invocation | Real Python child process output, timeout, cancellation and output cap exercised. |
| OPA release binary | `tmp/opa/opa_windows_amd64.exe version` | Version1.22.4, Windows/amd64, Rego v1. Official asset SHA256 matched `4cd179b95041aa50c44241324da3becf35d0b28dca92bf10a07f32d002724d5e`. |
| OPA policy syntax | `tmp/opa/opa_windows_amd64.exe check integrations/policies/governance.rego` | Exit0, no diagnostics. This is syntax/type validation, not a service integration test. |
| OPA image | `docker pull openpolicyagent/opa:1.22.4-static` | Downloaded successfully, digest `sha256:12cecac5a174368f7d3f09d3a19d040ebe0c91d576e520335ae7a985a26e39d3`. |

Run unit/application checks from repository root with `PYTHONPATH=backend` set in the environment:

```text
python -m pytest tests/test_security_adapters.py -q
```

The recorded result is **8 passed, 1 skipped**. The skip is the real OPA service test, which requires `TEST_OPA_URL`; no mock service is substituted. A deliberately mocked malformed Presidio response tests parser rejection in isolation and is not a connectivity claim. A Starlette notice recommends migrating the test client's HTTP library in a future dependency update. See the release status for the final complete-suite result.

## Runtime deployment contract

`OPA_URL`, `PRESIDIO_ANALYZER_URL` and `PRESIDIO_ANONYMIZER_URL` are trusted deployment settings, not tenant configuration. Only HTTP(S) origins are accepted. The adapter fixes endpoint paths, disables redirects and environment proxy use, caps response size, and applies bounded HTTP timeouts. Optional server credentials come from the corresponding deployment variable ending in `_TOKEN`; they are not returned by the API.

OPA expects the application-owned policy at `integrations/policies/governance.rego`, loaded at startup. The only evaluated path is `/v1/data/uag/decision`. The policy evaluates supplied risk/PII/approval metadata; it is not an AI risk classifier and does not verify the truth of these inputs. Missing classification yields review. Unacceptable risk and unauthorized PII produce block; high risk needs explicit approval. No tenant-authored Rego, executable actions, arbitrary policy path, or network built-in is accepted.

For a supported Docker host, use the verified image above, a read-only mount to `/policies`, and arguments:

```text
run --server --addr=0.0.0.0:8181 /policies/governance.rego
```

Keep the policy/data control plane on an internal network; do not expose its management API publicly. The root Compose configuration owns service resource limits and networking. Set `TEST_OPA_URL` to the reachable test service to enable actual allow/block/review assertions. Health checks alone do not prove decision correctness.

Presidio uses the verified analyzer `/analyze` and anonymizer `/anonymize` contracts from release2.2.366. `/health` returns text. No recognizer or model coverage is assumed until an operator deploys and validates a specific service. Model licences are separate. Prompt text is omitted from adapter logs and raw response; anonymized output is returned when requested. The application's job persistence/retention policy still governs submitted inputs.

Both runtime adapters have explicit `error_action` values of `block` or `review`; failures never silently become allow. OPA and Presidio execute asynchronously through integration jobs. No sub-50ms claim is made for either component or proxy path.

## Signing and format boundaries

Evidence is UTF-8 text, JSON, safe-parsed XML or CSV, with a2MB byte cap. It is stored in the tenant database; no arbitrary filesystem paths are accepted. Binary/model/pickle uploads are not supported. JSON OSCAL catalogue, profile, component definition, SSP, assessment plan/results and POA&M validation delegates to installed Trestle models. Only catalogue fixtures have been independently tested here. XML is checked for safe XML syntax only and is not claimed as OSCAL validated. External OSCAL links are not fetched.

`SIGNING_KEY_PATH` points to an operator-provisioned Ed25519 PEM outside source control. The evidence route refuses signing when the key is absent. DSSE signs its exact pre-authentication encoding; verification trusts the configured key and binds both evidence digest and evidence identifier. The statement uses an application-owned predicate URI, not a SLSA predicate. No public transparency log or external signing service is contacted. The public fingerprint appears in attestations; private key bytes never appear in API output. Key rotation currently requires retaining the previous trusted key for historical verification; a multi-key/KMS trust store is remaining work.

Evidence hashes and DSSE establish byte integrity and signer trust within the configured local trust policy. They do not prove factual truth of an artefact. The audit chain detects ordinary edits but privileged database access can rewrite the database; immutable external storage is not implemented.

## Outstanding blockers and licences

Docker container creation failed with `write /var/lib/desktop-containerd/daemon/io.containerd.metadata.v1.bolt/meta.db: read-only file system`. A combined background OPA service launch was rejected by automatic approval policy with `blocked by policy`; the action was not retried through an alternative runner. Read-only version and policy checks were subsequently permitted. Consequently OPA service, OPA-Envoy and Envoy container startup and latency remain unverified.

Cosign execution is awaiting a separately configured signing workflow. NeMo requires a Python version below3.14 for the verified stable release and a reviewed model/configuration. AI Verify requires an approved plugin, model and dataset; unsafe model deserialization is excluded. aigrc real endpoint evaluation requires provider configuration; its offline examples are mocks and have not been presented as runtime results.

VerifyWise current HEAD uses VCEL1.0 (October2026), replacing BSL1.1 for new releases. Intended commercial client production/hosting/redistribution requires separate written authorization. Its entry remains licence restricted. PurpleLlama is mixed-license: MIT evaluation/code components and model-specific Llama Community terms. No model terms were accepted and no weights downloaded.
