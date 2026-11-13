# Third-party notices

No upstream source trees are vendored. Research records contain attribution, source URLs and hashes. Dependencies are installed through package managers or separately deployed services. Preserve upstream package licence and NOTICE files in distributions.

- **OWASP cdxgen** — https://github.com/cdxgen/cdxgen. Apache-2.0; preserve licence/notices and dependency licences
- **OWASP AIBOM Generator** — https://github.com/GenAI-Security-Project/aibom-generator. Apache-2.0 stated in licence and manifest; model/dataset licences remain separate
- **OpenComplAI Scan** — https://github.com/opencomplai/opencomplai. AGPL-3.0-only Community Edition; network-use/source obligations must be assessed before embedding or hosted deployment; commercial Enterprise licence offered
- **RiskForge by AI Exponent** — https://github.com/aiexponent/riskforge. Apache-2.0; preserve notices and review dependent libraries
- **EU AI Act Toolkit (AbdelStark)** — https://github.com/AbdelStark/eu-ai-act-toolkit. MIT; retain copyright and licence if source is redistributed
- **Venturalitica SDK** — https://github.com/Venturalitica/venturalitica-sdk. Apache-2.0; model/cloud terms separate
- **COMPL-AI** — https://github.com/compl-ai/compl-ai. Apache-2.0 main project; benchmark datasets, models and third-party tasks have separate licences
- **Awesome EU AI Act** — https://github.com/morganrcu/awesome-eu-ai-act. README dedicates work under CC0-1.0; linked projects retain their own terms
- **ISO/IEC 42001 AI Governance Toolkit (Ankit Uniyal)** — https://github.com/Ankit-Uniyal/iso-42001-ai-governance-toolkit. MIT for toolkit repository. This does not grant rights to reproduce ISO/IEC standard text or claim certification.
- **EU AI Act Compliance Toolkit (Ankit Uniyal)** — https://github.com/Ankit-Uniyal/eu-ai-act-compliance-toolkit. UNVERIFIED: LICENSE, LICENSE.md and LICENSE.txt return 404; GitHub root file listing shows no licence. pyproject says See repository LICENSE. Public source alone is not a reuse grant.
- **IBM AI Atlas Nexus (formerly Risk Atlas Nexus)** — https://github.com/IBM/ai-atlas-nexus. Apache-2.0 main repository; imported taxonomy and model terms require per-artifact review
- **NIST AI Resource Center / AI RMF** — https://airc.nist.gov. US government reference material subject to NIST site terms; third-party material and trademarks retain their rights
- **M3 Framework** — https://m3framework.org. CC-BY-4.0 standard text; Apache-2.0 code/data. Attribute Julius Gromyko and indicate changes. Trademarks reserved; no official-partner or M3-Certified claim.
- **OSCAL Compass** — https://github.com/oscal-compass/community. Community README identifies Apache-2.0; components require individual review. No upstream code bundled.
- **Compliance Trestle** — https://github.com/oscal-compass/compliance-trestle. Apache-2.0; preserve licence and notices when distributing package. No product-specific commercial prohibition identified.
- **Sigstore Cosign** — https://github.com/sigstore/cosign. Apache-2.0; preserve notices. Public transparency log terms and identity publication require deliberate operator choice.
- **in-toto Attestation Framework** — https://github.com/in-toto/attestation. Apache-2.0. Other predicate specifications may have separate licences.
- **aigrc** — https://github.com/connectsmartconsulting/aigrc. MIT for repository code; proprietary methodology/services explicitly excluded from MIT code grant.
- **Open Policy Agent + OPA-Envoy Plugin** — https://github.com/open-policy-agent/opa. Apache-2.0 for both OPA and OPA-Envoy; preserve notices.
- **Envoy Proxy** — https://github.com/envoyproxy/envoy. Apache-2.0; preserve notices and audit image dependencies.
- **AI Verify Toolkit** — https://github.com/IMDA-BTG/aiverify. Apache-2.0 for repository; stock plugins/dependencies require additional review.
- **VerifyWise** — https://github.com/bluewave-labs/verifywise. CURRENT HEAD: VerifyWise Community & Evaluation License (VCEL) 1.0, October 2026, replaces BSL1.1 for new releases. Commercial organizational production use, hosting and redistribution require separate written authorization. Companies may evaluate for 60 days; qualifying personal/education/government/noncommercial uses have distinct grants. Existing releases retain their release licence. No commercial permission assumed.
- **Presidio (originally Microsoft Presidio)** — https://github.com/microsoft/presidio. MIT for Presidio code; NLP model licences and external service terms need separate review.
- **NVIDIA NeMo Guardrails** — https://github.com/NVIDIA/NeMo-Guardrails. Apache-2.0 code; model/provider and optional integration licences separate.
- **Meta Purple Llama / Llama Guard** — https://github.com/meta-llama/PurpleLlama. Mixed licences: MIT evals/benchmarks/Code Shield; Llama models use model-specific Llama Community licences, not MIT. Current root LICENSE is Llama3.2 Community Agreement with attribution, acceptable-use and >700M monthly active user terms. README model/link inconsistencies mean recheck exact model repository licence before use.

## Optional English NLP model

Presidio and spaCy are MIT. en_core_web_sm 3.8.0 is distributed under its MIT model licence. Its source notices identify OntoNotes 5 (commercial training-data licence held by Explosion), WordNet and other attributions; no training corpus is redistributed here. Model weights are downloaded from the official release only during the optional image build, with a pinned SHA256. See [model licence](docs/third-party/spacy-en_core_web_sm-LICENSE.txt) and [source notices](docs/third-party/spacy-en_core_web_sm-LICENSES_SOURCES.txt). This licence does not grant access to the original training corpus.

Installed distributions retain their own bundled licence files. Python inventory: docs/dependency-inventory.json; optional service inventory: docs/release/presidio-dependencies.json; npm inventories: both package-lock.json files. Base image OS packages retain Debian/Alpine licences and notices.

PostgreSQL's derived image uses Alpine su-exec 0.3-r0 (MIT, https://github.com/ncopa/su-exec) in place of gosu. Its package licence metadata remains in the image. No source is copied into this repository.
