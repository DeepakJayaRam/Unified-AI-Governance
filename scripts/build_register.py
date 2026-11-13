"""Regenerate readable catalogue/audit from inspected source records."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
items = sum((json.loads((root / "docs/research" / filename).read_text(encoding="utf-8")) for filename in ("governance.json", "security.json")), [])
assert len(items) == 25 and {row["number"] for row in items} == set(range(1, 26))
(root / "integrations/catalog.json").write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
lines = ["# Integration register", "", "Reverified 2026-11-13 against official sources. Five tested executable entries, five reference resources, eleven deferred entries and four entries restricted pending licence review. No adapter-only or unsupported entries are claimed. OPA-Envoy remains deferred within entry 19. See docs/release/VERIFICATION.md for executable scope.", "", "| # | Layer | Upstream | Release classification | Inspected version/revision | Execution evidence |", "|---|---|---|---|---|---|"]
licences = ["# Licence audit", "", "Original application code: Apache-2.0. External components retain their own licences. This engineering audit is not a substitute for legal review of intended distribution and service operation.", "", "VerifyWise current VCEL1.0 restricts the intended commercial client deployment; it is blocked. OpenComplAI AGPL obligations require separate review before distribution/service integration. Missing or ambiguous licence evidence blocks copying or executable inclusion. ISO normative text is not included.", "", "| # | Upstream | Observed licence and restrictions | Decision |", "|---|---|---|---|"]
notices = ["# Third-party notices", "", "No upstream source trees are vendored. Research records contain attribution, source URLs and hashes. Dependencies are installed through package managers or separately deployed services. Preserve upstream package licence and NOTICE files in distributions.", ""]
for row in items:
    version = row.get("version", row.get("latest_release", row.get("inspected_revision", "See detailed record")))
    test = row.get("test_status", row.get("integration_test_status", "Not executed"))
    lines.append(f"| {row['number']} | {row['layer']} | [{row['name']}]({row['source_url']}) | {row['release_classification']} | {str(version).replace('|', '/')} | {test} |")
    licences.append(f"| {row['number']} | {row['name']} | {str(row['licence']).replace('|', '/')} | {row['classification']} |")
    notices.append(f"- **{row['name']}** — {row['source_url']}. {row['licence']}")
lines += ["", "Detailed records: [layers1–4](docs/research/governance.json), [layers5–7](docs/research/security.json). Historical research narratives are retained; the current source and licence recheck is docs/release/upstream-reverification.json. Catalogue changes do not automatically enable adapters."]
notices += ["", "## Optional English NLP model", "", "Presidio and spaCy are MIT. en_core_web_sm 3.8.0 is distributed under its MIT model licence. Its source notices identify OntoNotes 5 (commercial training-data licence held by Explosion), WordNet and other attributions; no training corpus is redistributed here. Model weights are downloaded from the official release only during the optional image build, with a pinned SHA256. See [model licence](docs/third-party/spacy-en_core_web_sm-LICENSE.txt) and [source notices](docs/third-party/spacy-en_core_web_sm-LICENSES_SOURCES.txt). This licence does not grant access to the original training corpus.", "", "Installed distributions retain their own bundled licence files. Python inventory: docs/dependency-inventory.json; optional service inventory: docs/release/presidio-dependencies.json; npm inventories: both package-lock.json files. Base image OS packages retain Debian/Alpine licences and notices."]
licences += ["", "The optional English model is MIT-distributed, with separate training-source notices preserved in docs/third-party. See THIRD_PARTY_NOTICES.md. No VerifyWise, OpenComplAI, unlicensed toolkit or Llama model source/weights are bundled."]
notices += ["", "PostgreSQL's derived image uses Alpine su-exec 0.3-r0 (MIT, https://github.com/ncopa/su-exec) in place of gosu. Its package licence metadata remains in the image. No source is copied into this repository."]
for name, content in (("INTEGRATION_REGISTER.md", lines), ("LICENCE_AUDIT.md", licences), ("THIRD_PARTY_NOTICES.md", notices)):
    (root / name).write_text("\n".join(content) + "\n", encoding="utf-8")
print("Generated 25-entry register, licence audit and upstream notices")
