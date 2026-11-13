# Governance and discovery upstream verification

Inspected 2026-11-13. GitHub API returned 403 (shared anonymous rate limit); commit IDs were obtained using `git ls-remote` and files were read from commit-pinned raw URLs. Source hashes are in `sources/governance-source-manifest.json`. This register distinguishes verified interfaces from executed integrations. Raw inspection files remain in ignored `tmp/`; no third-party source is vendored.

Current EU legal interpretation must use [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) together with applicable amendments, including [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj), whose official EUR-Lex record was verified in force. Do not derive legal deadlines or certification claims from a toolkit README. ISO standard text is not reproduced.

## 1. OWASP cdxgen

**Layer:** 1

**Source url:** https://github.com/cdxgen/cdxgen

**Classification:** CLI_INTEGRATION

**Version:** npm stable 13.7.0; inspected HEAD manifest 13.8.0 (not selected)

**Inspected commit:** 0bf437ead5043f40e51ffae5f662eb47f8febba4

**Verified at:** 2026-11-13

**Capabilities:** Generate CycloneDX inventory from source manifests and supported ecosystems; AI/ML inventory depends on discovered metadata; an SBOM is not proof of all AI usage

**Languages:** JavaScript; TypeScript; Python helper metadata

**Installation:** cd integrations/tooling && npm ci --ignore-scripts --omit=optional; Node >=24.15, tested 24.22.3; lockfile pins cdxgen13.7.0 and patched glob14.0.6/minimatch11.0.8 overrides

**Dependencies:** Node >=24; Ecosystem-specific tools for richer analysis; Optional platform plugins

**Api:** Optional server mode documented; no network service selected

**Sdk:** JavaScript package exports verified in package.json

**Cli:** cdxgen and aibom binaries verified

**Deployment:** Official container documented; local restricted CLI selected

**Input formats:** package manifests; lock files; source trees; supported container inputs

**Output formats:** CycloneDX JSON

**Licence:** Apache-2.0; preserve licence/notices and dependency licences

**Maintenance:** Repository accessible. Stable npm and development HEAD differ; pin stable. Language coverage varies with installed toolchains.

**Integration method:** Implemented restricted npm v3 lockfile CLI adapter. Node filesystem permissions deny child processes and addons; staged data only, no install scripts; background execution only.

**Security risks:** Dependency scripts and external tool invocation; Source/manifest secrets in output; Resource exhaustion; Do not equate inventory with vulnerability detection

**Test status:** REAL_EXECUTION_PASSED: 11 adapter/security tests; cdxgen 13.7.0 generated schema-validated CycloneDX 1.6 from an explicit npm v3 fixture; see docs/verification/cdxgen-test.json

**Sources:** [source 1](https://raw.githubusercontent.com/cdxgen/cdxgen/0bf437ead5043f40e51ffae5f662eb47f8febba4/README.md), [source 2](https://raw.githubusercontent.com/cdxgen/cdxgen/0bf437ead5043f40e51ffae5f662eb47f8febba4/LICENSE), [source 3](https://raw.githubusercontent.com/cdxgen/cdxgen/0bf437ead5043f40e51ffae5f662eb47f8febba4/pyproject.toml), [source 4](https://raw.githubusercontent.com/cdxgen/cdxgen/0bf437ead5043f40e51ffae5f662eb47f8febba4/package.json), [source 5](https://raw.githubusercontent.com/cdxgen/cdxgen/0bf437ead5043f40e51ffae5f662eb47f8febba4/bin/cdxgen.js), [source 6](https://registry.npmjs.org/@cdxgen%2fcdxgen/latest)

## 2. OWASP AIBOM Generator

**Layer:** 1

**Source url:** https://github.com/GenAI-Security-Project/aibom-generator

**Classification:** DEFERRED

**Version:** HEAD pyproject 1.0.2; PyPI name owasp-aibom-generator returned 404

**Inspected commit:** 45851cb96dbe16209f29c88fc3f5b9d9d19ecf7e

**Verified at:** 2026-11-13

**Capabilities:** Extract Hugging Face model metadata; Generate CycloneDX 1.6 JSON; AIBOM completeness scoring

**Languages:** Python; HTML

**Installation:** Upstream documents pip install -r requirements.txt or uv sync from source; python -m src.cli owner/model

**Dependencies:** Python >=3.11; cyclonedx-python-lib; huggingface_hub; torch; transformers; datasets

**Api:** README declares API endpoints; precise interface not yet exercised

**Sdk:** Source Python modules, no independently verified SDK contract

**Cli:** src.cli and aibom entry point verified

**Deployment:** python -m src.main documented; no production deployment validated

**Input formats:** Hugging Face model ID; optional metadata overrides

**Output formats:** CycloneDX 1.6 JSON; completeness metrics

**Licence:** Apache-2.0 stated in licence and manifest; model/dataset licences remain separate

**Maintenance:** Repository accessible. Heavy dependencies and unpublished package name require isolated source build and runtime tests.

**Integration method:** Await isolated service deployment, model egress allowlist and contract test; catalogue link available.

**Security risks:** Model repository untrusted metadata; Remote inference option requires credentials; Large downloads; PII or confidential model IDs sent externally

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/GenAI-Security-Project/aibom-generator/45851cb96dbe16209f29c88fc3f5b9d9d19ecf7e/README.md), [source 2](https://raw.githubusercontent.com/GenAI-Security-Project/aibom-generator/45851cb96dbe16209f29c88fc3f5b9d9d19ecf7e/LICENSE), [source 3](https://raw.githubusercontent.com/GenAI-Security-Project/aibom-generator/45851cb96dbe16209f29c88fc3f5b9d9d19ecf7e/pyproject.toml), [source 4](https://raw.githubusercontent.com/GenAI-Security-Project/aibom-generator/45851cb96dbe16209f29c88fc3f5b9d9d19ecf7e/requirements.txt)

## 3. OpenComplAI Scan

**Layer:** 1

**Source url:** https://github.com/opencomplai/opencomplai

**Classification:** DEFERRED

**Version:** opencomplai-cli 0.15.0 (PyPI 2026-11-08)

**Inspected commit:** 455be2575d728dff6070f87f80489da5fb5c7b05

**Verified at:** 2026-11-13

**Capabilities:** Deterministic code/manifest discovery and findings; Compliance manifest checks; EU AI Act evaluated; NIST projection and attestation-led framework packs are distinct; Scanner advisory mode documented; check exit codes have different semantics

**Languages:** Python; TypeScript

**Installation:** Upstream: pip install opencomplai-cli==0.15.0; not bundled by this application

**Dependencies:** Python >=3.11; opencomplai-core; Typer; Rich; Pydantic

**Api:** Separate gateway/services documented; not configured

**Sdk:** opencomplai Python SDK package exists

**Cli:** opencomplai scan --quick and scan --manifest ... --repo-root ... documented

**Deployment:** Upstream Compose exists under infra/compose; separate deployment only pending licence assessment

**Input formats:** Repository files; system-manifest.json; scan baseline JSON

**Output formats:** scan-report.json; compliance-artifact.json; structured findings

**Licence:** AGPL-3.0-only Community Edition; network-use/source obligations must be assessed before embedding or hosted deployment; commercial Enterprise licence offered

**Maintenance:** Accessible active source; stable CLI verified through PyPI. Documentation explicitly distinguishes discovery and compliance gates.

**Integration method:** Deferred pending AGPL distribution/network obligation decision and isolated CLI tests. No source copied or package included.

**Security risks:** Scan can read sensitive files; use .ocignore plus app staging allowlist; Optional push and model inference must remain disabled; Advisory findings are not compliance certification

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/README.md), [source 2](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/LICENSE), [source 3](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/pyproject.toml), [source 4](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/package.json), [source 5](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/setup.py), [source 6](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/packages/cli/pyproject.toml), [source 7](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/docs/src/getting-started/scanner.md), [source 8](https://raw.githubusercontent.com/opencomplai/opencomplai/455be2575d728dff6070f87f80489da5fb5c7b05/docs/src/guides/ci-integration.md), [source 9](https://pypi.org/pypi/opencomplai-cli/json)

## 4. RiskForge by AI Exponent

**Layer:** 2

**Source url:** https://github.com/aiexponent/riskforge

**Classification:** DEFERRED

**Version:** riskforge 2.1.0 (PyPI 2026-11-07)

**Inspected commit:** d823d1a1435251d41e9edce8701214eb65361ab8

**Verified at:** 2026-11-13

**Capabilities:** Guided Article 9 risk assessment; Risk Management File exports; Hash-chained audit trail and verification features; Human input drives assessment; no legal certification

**Languages:** Python

**Installation:** pip install riskforge==2.1.0 in separate environment; PDF requires platform libraries described upstream

**Dependencies:** Python >=3.11; Typer <0.26; Pydantic 2; WeasyPrint 70; cryptography; PyYAML; jsonschema

**Api:** No supported HTTP service verified

**Sdk:** Python modules and plugin entry points; no stable external SDK contract validated

**Cli:** riskforge CLI verified in manifest; init, assess and export workflows documented

**Deployment:** Local offline CLI; PDF system dependencies require separate packaging

**Input formats:** System metadata; guided answers; YAML answers; imported evidence JSON

**Output formats:** Risk Management File JSON; Markdown; PDF

**Licence:** Apache-2.0; preserve notices and review dependent libraries

**Maintenance:** Actual repo aiexponent/riskforge verified by PyPI project URLs. Website snippets can lag current package; dependency bounds matter.

**Integration method:** Await isolated CLI installation and noninteractive workflow contract tests; native application assessment stores evidence meanwhile.

**Security risks:** Local audit files contain sensitive risk information; Plugin code execution; PDF resource loading; Hash chains alone do not prevent privileged tampering

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/aiexponent/riskforge/d823d1a1435251d41e9edce8701214eb65361ab8/README.md), [source 2](https://raw.githubusercontent.com/aiexponent/riskforge/d823d1a1435251d41e9edce8701214eb65361ab8/LICENSE), [source 3](https://raw.githubusercontent.com/aiexponent/riskforge/d823d1a1435251d41e9edce8701214eb65361ab8/pyproject.toml), [source 4](https://pypi.org/pypi/riskforge/json)

## 5. EU AI Act Toolkit (AbdelStark)

**Layer:** 2

**Source url:** https://github.com/AbdelStark/eu-ai-act-toolkit

**Classification:** DEFERRED

**Version:** Source SDK and CLI 0.1.0; both npm package latest URLs returned 404

**Inspected commit:** fff58f6e890648947ba9f9a8caeb94bd566c4651

**Verified at:** 2026-11-13

**Capabilities:** Deterministic TypeScript classification and checklists; Markdown templates with placeholders; CLI JSON reports; Static browser workspace

**Languages:** TypeScript; JavaScript

**Installation:** README proposes npm @eu-ai-act/sdk and npx @eu-ai-act/cli, but registry 404 observed; source build requires npm install then turbo build

**Dependencies:** Node >=20; TypeScript; Turborepo; SDK manifest has no runtime dependencies

**Api:** No backend API; web app is client-side

**Sdk:** Source @eu-ai-act/sdk exists; registry installation not verified

**Cli:** Source @eu-ai-act/cli exists; registry installation not verified

**Deployment:** Static Next.js app and local CLI source; no container verified

**Input formats:** Classification questionnaire; risk tier; template metadata

**Output formats:** Classification JSON; checklist JSON; Markdown templates

**Licence:** MIT; retain copyright and licence if source is redistributed

**Maintenance:** Source accessible; advertised published package availability failed. README legal dates differ from 2026 EUR-Lex amendment; review content before reuse.

**Integration method:** Reference link and native assessment workflow now; defer package adapter until source-built artifact and legal mappings validated.

**Security risks:** Classification may omit legal exceptions; Stale regulatory dates; Do not automatically treat score as compliance

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/AbdelStark/eu-ai-act-toolkit/fff58f6e890648947ba9f9a8caeb94bd566c4651/README.md), [source 2](https://raw.githubusercontent.com/AbdelStark/eu-ai-act-toolkit/fff58f6e890648947ba9f9a8caeb94bd566c4651/LICENSE), [source 3](https://raw.githubusercontent.com/AbdelStark/eu-ai-act-toolkit/fff58f6e890648947ba9f9a8caeb94bd566c4651/package.json), [source 4](https://raw.githubusercontent.com/AbdelStark/eu-ai-act-toolkit/fff58f6e890648947ba9f9a8caeb94bd566c4651/packages/sdk/package.json), [source 5](https://raw.githubusercontent.com/AbdelStark/eu-ai-act-toolkit/fff58f6e890648947ba9f9a8caeb94bd566c4651/packages/cli/package.json), [source 6](https://registry.npmjs.org/@eu-ai-act%2fsdk/latest), [source 7](https://registry.npmjs.org/@eu-ai-act%2fcli/latest)

## 6. Venturalitica SDK

**Layer:** 2

**Source url:** https://github.com/Venturalitica/venturalitica-sdk

**Classification:** DEFERRED

**Version:** venturalitica 0.8.2 (PyPI 2026-08-27)

**Inspected commit:** dc64f520a786b9f5dfd4cebfa900b2847c9f3061

**Verified at:** 2026-11-13

**Capabilities:** Training-time data/fairness policy checks; Trace and model-BOM evidence; OSCAL policy and result workflows claimed upstream; Regulatory documentation drafts

**Languages:** Python

**Installation:** pip install venturalitica==0.8.2; disable analytics with VENTURALITICA_NO_ANALYTICS=1 or DO_NOT_TRACK

**Dependencies:** Python >=3.11; numpy >=2.4; pandas; scikit-learn; compliance-trestle; cyclonedx-python-lib; posthog

**Api:** No hosted API used; cloud described as forthcoming

**Sdk:** vl.enforce, vl.monitor, vl.retain documented

**Cli:** vl / venturalitica entry points verified

**Deployment:** Local SDK; optional dashboard and model extras

**Input formats:** pandas DataFrame; OSCAL policy YAML; training artifacts

**Output formats:** Audit trace JSON; CycloneDX ML-BOM; OSCAL assessment-results claimed; not validated here

**Licence:** Apache-2.0; model/cloud terms separate

**Maintenance:** Beta classifier in package manifest. Version verified; heavy scientific dependencies should be isolated from core.

**Integration method:** Deferred to data-science worker after representative dataset and OSCAL format tests; never claim compatibility from README alone.

**Security risks:** Telemetry enabled unless opted out; Optional cloud fallback for LLM generation; Potential sensitive dataset/evidence traces; Heavy CPU/GPU processing

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/Venturalitica/venturalitica-sdk/dc64f520a786b9f5dfd4cebfa900b2847c9f3061/README.md), [source 2](https://raw.githubusercontent.com/Venturalitica/venturalitica-sdk/dc64f520a786b9f5dfd4cebfa900b2847c9f3061/LICENSE), [source 3](https://raw.githubusercontent.com/Venturalitica/venturalitica-sdk/dc64f520a786b9f5dfd4cebfa900b2847c9f3061/pyproject.toml), [source 4](https://pypi.org/pypi/venturalitica/json)

## 7. COMPL-AI

**Layer:** 2

**Source url:** https://github.com/compl-ai/compl-ai

**Classification:** DEFERRED

**Version:** HEAD pyproject 2.0.0; no tagged stable release found by git ls-remote

**Inspected commit:** c359f0a61112f8316715ea1c6e140983f0c50a40

**Verified at:** 2026-11-13

**Capabilities:** LLM technical benchmark suite built on Inspect AI; Provider API and local model evaluations; Sample-level evaluation logs; v1 and v2 scores not directly comparable

**Languages:** Python

**Installation:** Upstream: source clone then uv sync, use complai eval provider/model; pin inspected commit when trialled

**Dependencies:** Python >=3.11,<3.14; Inspect AI; PyTorch; datasets; spaCy; multiple Git-sourced packages; provider credentials or local model hardware

**Api:** Provider APIs consumed, not an application governance API

**Sdk:** Inspect AI task plugins

**Cli:** complai eval/list/samples/predict documented

**Deployment:** Separate evaluation environment; agentic tasks may use sandboxes

**Input formats:** Model/provider ID; task YAML/JSON; datasets

**Output formats:** Inspect evaluation logs; JSONL samples; predicted score JSON

**Licence:** Apache-2.0 main project; benchmark datasets, models and third-party tasks have separate licences

**Maintenance:** Accessible; framework mapping update in progress per README. Python 3.14 host incompatible with current declared bound.

**Integration method:** Asynchronous isolated evaluation only; awaiting Python <=3.13 environment and model/provider configuration.

**Security risks:** Cost and remote data transfer; GPU/CPU and sandbox requirements; Untrusted benchmark content; Benchmark score is not legal conformity

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/compl-ai/compl-ai/c359f0a61112f8316715ea1c6e140983f0c50a40/README.md), [source 2](https://raw.githubusercontent.com/compl-ai/compl-ai/c359f0a61112f8316715ea1c6e140983f0c50a40/LICENSE), [source 3](https://raw.githubusercontent.com/compl-ai/compl-ai/c359f0a61112f8316715ea1c6e140983f0c50a40/pyproject.toml)

## 8. Awesome EU AI Act

**Layer:** 2

**Source url:** https://github.com/morganrcu/awesome-eu-ai-act

**Classification:** REFERENCE_RESOURCE

**Version:** Commit inspected; no versioned executable release

**Inspected commit:** d46c0492aecea2e8b1e3496a1b8eb331c60193cb

**Verified at:** 2026-11-13

**Capabilities:** Curated links to EU AI Act resources, tools and frameworks

**Languages:** Markdown

**Installation:** No installation; visit or pin reference URL

**Dependencies:**

**Api:** None

**Sdk:** None

**Cli:** None

**Deployment:** Static repository reference

**Input formats:**

**Output formats:** Human-readable reference links

**Licence:** README dedicates work under CC0-1.0; linked projects retain their own terms

**Maintenance:** Repository accessible. Curated third-party claims require independent verification.

**Integration method:** Reference catalogue only; not executable and never shown as connected.

**Security risks:** Link rot; Non-authoritative legal summaries; Linked tools may have incompatible licences

**Test status:** REFERENCE_VERIFIED_NOT_EXECUTABLE

**Sources:** [source 1](https://raw.githubusercontent.com/morganrcu/awesome-eu-ai-act/d46c0492aecea2e8b1e3496a1b8eb331c60193cb/README.md)

## 9. ISO/IEC 42001 AI Governance Toolkit (Ankit Uniyal)

**Layer:** 3

**Source url:** https://github.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit

**Classification:** REFERENCE_RESOURCE

**Version:** Commit inspected; assessment checker 1.1.0, SoA tracker 1.0.0 in source; no project release tag

**Inspected commit:** 803b62da4c66f6b6ab601c87cb298597a497eebd

**Verified at:** 2026-11-13

**Capabilities:** AIMS templates and registers; Gap-assessment guidance and cross-framework references; CSV assessment-age checker; JSON SoA progress tracker with CSV export

**Languages:** Markdown; Python

**Installation:** Reference documents need no install. Optional upstream scripts use Python standard library; scripts not bundled.

**Dependencies:** Python standard library for optional scripts; Licensed ISO standard for authoritative requirements

**Api:** None verified

**Sdk:** None verified

**Cli:** 15-SCRIPTS/ai_assessment_checker.py and aims_soa_tracker.py inspected

**Deployment:** Documents and local optional scripts; no service

**Input formats:** CSV system assessment dates; SoA JSON state; human-entered governance records

**Output formats:** Text assessment report; SoA JSON; CSV

**Licence:** MIT for toolkit repository. This does not grant rights to reproduce ISO/IEC standard text or claim certification.

**Maintenance:** Source accessible. README indexes current files; feature counts are upstream claims, not independently audited ISO completeness.

**Integration method:** Reference catalogue; native AIMS register stores user decisions and original short prompts, without copying ISO clauses.

**Security risks:** Sensitive registers; Template/standard rights distinction; Do not claim full standard coverage or certification

**Test status:** REFERENCE_VERIFIED_NOT_EXECUTABLE

**Sources:** [source 1](https://raw.githubusercontent.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit/803b62da4c66f6b6ab601c87cb298597a497eebd/README.md), [source 2](https://raw.githubusercontent.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit/803b62da4c66f6b6ab601c87cb298597a497eebd/LICENSE), [source 3](https://raw.githubusercontent.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit/803b62da4c66f6b6ab601c87cb298597a497eebd/15-SCRIPTS/ai_assessment_checker.py), [source 4](https://raw.githubusercontent.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit/803b62da4c66f6b6ab601c87cb298597a497eebd/15-SCRIPTS/aims_soa_tracker.py)

## 10. EU AI Act Compliance Toolkit (Ankit Uniyal)

**Layer:** 3

**Source url:** https://github.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit

**Classification:** DEFERRED

**Version:** README heading 3.5.0; footer 3.4.0; pyproject classifier 2.1.0; README script 2.2; commit is authoritative identifier

**Inspected commit:** 8c57fa493d53d2b62b1b1ef82d3d4dedea41a7e7

**Verified at:** 2026-11-13

**Capabilities:** Governance templates and scorecards; Risk-tier classifier source; CSV inventory processing with JSON/text/CSV reports

**Languages:** Markdown; Python

**Installation:** Do not install or copy until a licence grant is located. Upstream documents python scripts/risk_classifier.py.

**Dependencies:** Python >=3.9; No package dependencies declared

**Api:** None verified

**Sdk:** None verified

**Cli:** eu-ai-risk-classify entry point in pyproject and source script documented

**Deployment:** Documents and local script; no service

**Input formats:** CSV AI inventory

**Output formats:** Text; JSON; CSV; Markdown templates

**Licence:** UNVERIFIED: LICENSE, LICENSE.md and LICENSE.txt return 404; GitHub root file listing shows no licence. pyproject says See repository LICENSE. Public source alone is not a reuse grant.

**Maintenance:** Source accessible but conflicting versions and missing licence prevent safe incorporation.

**Integration method:** External reference link only. Defer script/template redistribution and adapter installation until licence resolved.

**Security risks:** Missing licence; Legal classification needs professional review; Conflicting versions; Never treat generated clearance certificate as legal approval

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit/8c57fa493d53d2b62b1b1ef82d3d4dedea41a7e7/README.md), [source 2](https://raw.githubusercontent.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit/8c57fa493d53d2b62b1b1ef82d3d4dedea41a7e7/pyproject.toml), [source 3](https://raw.githubusercontent.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit/8c57fa493d53d2b62b1b1ef82d3d4dedea41a7e7/CHANGELOG.md), [source 4](https://raw.githubusercontent.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit/8c57fa493d53d2b62b1b1ef82d3d4dedea41a7e7/scripts/README.md)

## 11. IBM AI Atlas Nexus (formerly Risk Atlas Nexus)

**Layer:** 4

**Source url:** https://github.com/IBM/ai-atlas-nexus

**Classification:** DEFERRED

**Version:** ai-atlas-nexus 1.2.5 (PyPI 2026-08-31)

**Inspected commit:** 58bb356a44fb7fdfd9a8a1db091dcd196b561dcd

**Verified at:** 2026-11-13

**Capabilities:** Risk and governance knowledge graph; Cross-taxonomy querying; Risk identification using optional LLM inference; JSON/YAML graph queries

**Languages:** Python

**Installation:** pip install ai-atlas-nexus==1.2.5 in isolated compatible environment; extras for chosen inference provider

**Dependencies:** LinkML; SSSOM; txtai; datasets; mellea; pyoxigraph; pyshacl; optional Ollama/vLLM/Watsonx

**Api:** Consumes model APIs; no standalone HTTP API selected

**Sdk:** Python AI Atlas Nexus APIs

**Cli:** ran and ran-extension entry points verified; ran query emits JSON/YAML

**Deployment:** Local package plus optional separate inference service

**Input formats:** Knowledge graph records; AI system/task descriptions; query filters

**Output formats:** JSON; YAML; risk/task identification records

**Licence:** Apache-2.0 main repository; imported taxonomy and model terms require per-artifact review

**Maintenance:** README Python target is stale; HEAD manifest >=3.11,<=3.14.7 while PyPI 1.2.5 declares <3.14.4. Validate exact environment before install.

**Integration method:** Deferred package/query worker until dependency lock, taxonomy provenance and representative query test; NIST reference linked now.

**Security risks:** Optional automatic model download; External provider credentials/data; Large model dependencies; Mappings do not establish equivalent compliance

**Test status:** SOURCE_VERIFIED_NOT_EXECUTED

**Sources:** [source 1](https://raw.githubusercontent.com/IBM/ai-atlas-nexus/58bb356a44fb7fdfd9a8a1db091dcd196b561dcd/README.md), [source 2](https://raw.githubusercontent.com/IBM/ai-atlas-nexus/58bb356a44fb7fdfd9a8a1db091dcd196b561dcd/LICENSE), [source 3](https://raw.githubusercontent.com/IBM/ai-atlas-nexus/58bb356a44fb7fdfd9a8a1db091dcd196b561dcd/pyproject.toml), [source 4](https://pypi.org/pypi/ai-atlas-nexus/json)

## 12. NIST AI Resource Center / AI RMF

**Layer:** 4

**Source url:** https://airc.nist.gov

**Classification:** REFERENCE_RESOURCE

**Version:** AI RMF 1.0 (2023) reference; website states revision in progress

**Inspected commit:** None

**Verified at:** 2026-11-13

**Capabilities:** Authoritative AI RMF Govern, Map, Measure, Manage guidance; Playbook and crosswalk resources

**Languages:** Web documents; PDF

**Installation:** No executable installation; use official resources

**Dependencies:**

**Api:** No integration API verified

**Sdk:** None

**Cli:** None

**Deployment:** Public reference website

**Input formats:**

**Output formats:** HTML; PDF; published crosswalk documents

**Licence:** US government reference material subject to NIST site terms; third-party material and trademarks retain their rights

**Maintenance:** Official site accessible 2026-11-13; AI RMF 1.0 revision notice observed.

**Integration method:** Authoritative reference links and explicit framework identifiers in native records; no executable integration claim.

**Security risks:** Reference updates require mapping review; Crosswalk does not imply certification

**Test status:** REFERENCE_VERIFIED_NOT_EXECUTABLE

**Sources:** [source 1](https://airc.nist.gov/)

## 13. M3 Framework

**Layer:** 4

**Source url:** https://m3framework.org

**Classification:** REFERENCE_RESOURCE

**Version:** Official website and repository commit inspected; no executable stable release identified

**Inspected commit:** bcc539de5f3d65bf9f60db3a29c060ca48d30028

**Verified at:** 2026-11-13

**Capabilities:** Mount, Monitor, Manage methodology; SME governance guidance; Mappings and templates for multiple frameworks

**Languages:** Documentation; CSV/JSON/YAML artifacts described by licence

**Installation:** No install required for reference use; visit official site and repository

**Dependencies:**

**Api:** No application API verified

**Sdk:** No SDK verified

**Cli:** No CLI verified

**Deployment:** Static website and reference repository

**Input formats:**

**Output formats:** Methodology text; reference mappings; templates

**Licence:** CC-BY-4.0 standard text; Apache-2.0 code/data. Attribute Julius Gromyko and indicate changes. Trademarks reserved; no official-partner or M3-Certified claim.

**Maintenance:** Official site and explicit 2026 licence grant verified. No executable interface demonstrated.

**Integration method:** Reference catalogue only. May evaluate separately versioned template import later with attribution.

**Security risks:** Trademark/endorsement claims; Mapping completeness; Do not treat framework use as ISO certification

**Test status:** REFERENCE_VERIFIED_NOT_EXECUTABLE

**Sources:** [source 1](https://raw.githubusercontent.com/juliusgromyko/M3Framework/bcc539de5f3d65bf9f60db3a29c060ca48d30028/LICENSE), [source 2](https://m3framework.org/), [source 3](https://m3framework.org/license.html)
