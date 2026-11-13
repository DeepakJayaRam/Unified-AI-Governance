# Licence audit

Original application code: Apache-2.0. External components retain their own licences. This engineering audit is not a substitute for legal review of intended distribution and service operation.

VerifyWise current VCEL1.0 restricts the intended commercial client deployment; it is blocked. OpenComplAI AGPL obligations require separate review before distribution/service integration. Missing or ambiguous licence evidence blocks copying or executable inclusion. ISO normative text is not included.

| # | Upstream | Observed licence and restrictions | Decision |
|---|---|---|---|
| 1 | OWASP cdxgen | Apache-2.0; preserve licence/notices and dependency licences | CLI_INTEGRATION |
| 2 | OWASP AIBOM Generator | Apache-2.0 stated in licence and manifest; model/dataset licences remain separate | DEFERRED |
| 3 | OpenComplAI Scan | AGPL-3.0-only Community Edition; network-use/source obligations must be assessed before embedding or hosted deployment; commercial Enterprise licence offered | DEFERRED |
| 4 | RiskForge by AI Exponent | Apache-2.0; preserve notices and review dependent libraries | DEFERRED |
| 5 | EU AI Act Toolkit (AbdelStark) | MIT; retain copyright and licence if source is redistributed | DEFERRED |
| 6 | Venturalitica SDK | Apache-2.0; model/cloud terms separate | DEFERRED |
| 7 | COMPL-AI | Apache-2.0 main project; benchmark datasets, models and third-party tasks have separate licences | DEFERRED |
| 8 | Awesome EU AI Act | README dedicates work under CC0-1.0; linked projects retain their own terms | REFERENCE_RESOURCE |
| 9 | ISO/IEC 42001 AI Governance Toolkit (Ankit Uniyal) | MIT for toolkit repository. This does not grant rights to reproduce ISO/IEC standard text or claim certification. | REFERENCE_RESOURCE |
| 10 | EU AI Act Compliance Toolkit (Ankit Uniyal) | UNVERIFIED: LICENSE, LICENSE.md and LICENSE.txt return 404; GitHub root file listing shows no licence. pyproject says See repository LICENSE. Public source alone is not a reuse grant. | BLOCKED_BY_LICENCE |
| 11 | IBM AI Atlas Nexus (formerly Risk Atlas Nexus) | Apache-2.0 main repository; imported taxonomy and model terms require per-artifact review | DEFERRED |
| 12 | NIST AI Resource Center / AI RMF | US government reference material subject to NIST site terms; third-party material and trademarks retain their rights | REFERENCE_RESOURCE |
| 13 | M3 Framework | CC-BY-4.0 standard text; Apache-2.0 code/data. Attribute Julius Gromyko and indicate changes. Trademarks reserved; no official-partner or M3-Certified claim. | REFERENCE_RESOURCE |
| 14 | OSCAL Compass | Community README identifies Apache-2.0; components require individual review. No upstream code bundled. | REFERENCE_RESOURCE |
| 15 | Compliance Trestle | Apache-2.0; preserve licence and notices when distributing package. No product-specific commercial prohibition identified. | PACKAGE_DEPENDENCY |
| 16 | Sigstore Cosign | Apache-2.0; preserve notices. Public transparency log terms and identity publication require deliberate operator choice. | DEFERRED |
| 17 | in-toto Attestation Framework | Apache-2.0. Other predicate specifications may have separate licences. | NATIVE_ADAPTER |
| 18 | aigrc | MIT for repository code; proprietary methodology/services explicitly excluded from MIT code grant. | DEFERRED |
| 19 | Open Policy Agent + OPA-Envoy Plugin | Apache-2.0 for both OPA and OPA-Envoy; preserve notices. | API_SERVICE |
| 20 | Envoy Proxy | Apache-2.0; preserve notices and audit image dependencies. | DEFERRED |
| 21 | AI Verify Toolkit | Apache-2.0 for repository; stock plugins/dependencies require additional review. | DEFERRED |
| 22 | VerifyWise | CURRENT HEAD: VerifyWise Community & Evaluation License (VCEL) 1.0, October 2026, replaces BSL1.1 for new releases. Commercial organizational production use, hosting and redistribution require separate written authorization. Companies may evaluate for 60 days; qualifying personal/education/government/noncommercial uses have distinct grants. Existing releases retain their release licence. No commercial permission assumed. | BLOCKED_BY_LICENCE |
| 23 | Presidio (originally Microsoft Presidio) | MIT for Presidio code; NLP model licences and external service terms need separate review. | API_SERVICE |
| 24 | NVIDIA NeMo Guardrails | Apache-2.0 code; model/provider and optional integration licences separate. | DEFERRED |
| 25 | Meta Purple Llama / Llama Guard | Mixed licences: MIT evals/benchmarks/Code Shield; Llama models use model-specific Llama Community licences, not MIT. Current root LICENSE is Llama3.2 Community Agreement with attribution, acceptable-use and >700M monthly active user terms. README model/link inconsistencies mean recheck exact model repository licence before use. | DEFERRED |

The optional English model is MIT-distributed, with separate training-source notices preserved in docs/third-party. See THIRD_PARTY_NOTICES.md. No VerifyWise, OpenComplAI, unlicensed toolkit or Llama model source/weights are bundled.
