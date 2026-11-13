"""Regenerate readable catalogue/audit from inspected source records."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
items = sum((json.loads((root / "docs/research" / filename).read_text(encoding="utf-8")) for filename in ("governance.json", "security.json")), [])
assert len(items) == 25 and {row["number"] for row in items} == set(range(1, 26))
(root / "integrations/catalog.json").write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
lines = ["# Integration register", "", "Verified 2026-11-13 from linked official source and package records. Presence is not proof of installed or tested execution. See individual records for all 18 research fields and precise uncertainty.", "", "| # | Layer | Upstream | Classification | Inspected version/revision | Execution evidence |", "|---|---|---|---|---|---|"]
licences = ["# Licence audit", "", "Original application code: Apache-2.0. External components retain their own licences. This engineering audit is not a substitute for legal review of intended distribution and service operation.", "", "VerifyWise current VCEL1.0 restricts the intended commercial client deployment; it is blocked. OpenComplAI AGPL obligations require separate review before distribution/service integration. Missing or ambiguous licence evidence blocks copying or executable inclusion. ISO normative text is not included.", "", "| # | Upstream | Observed licence and restrictions | Decision |", "|---|---|---|---|"]
notices = ["# Third-party notices", "", "No upstream source trees are vendored. Research records contain attribution, source URLs and hashes. Dependencies are installed through package managers or separately deployed services. Preserve upstream package licence and NOTICE files in distributions.", ""]
for row in items:
    version = row.get("version", row.get("latest_release", row.get("inspected_revision", "See detailed record")))
    test = row.get("test_status", row.get("integration_test_status", "Not executed"))
    lines.append(f"| {row['number']} | {row['layer']} | [{row['name']}]({row['source_url']}) | {row['classification']} | {str(version).replace('|', '/')} | {test} |")
    licences.append(f"| {row['number']} | {row['name']} | {str(row['licence']).replace('|', '/')} | {row['classification']} |")
    notices.append(f"- **{row['name']}** — {row['source_url']}. {row['licence']}")
lines += ["", "Detailed records: [layers1–4](docs/research/governance.md), [layers5–7](docs/research/security.md). Machine-readable JSON accompanies each. GitHub REST metadata was rate-limited; archive/maintenance assertions are limited to evidence explicitly recorded. Catalogue changes do not automatically enable adapters."]
for name, content in (("INTEGRATION_REGISTER.md", lines), ("LICENCE_AUDIT.md", licences), ("THIRD_PARTY_NOTICES.md", notices)):
    (root / name).write_text("\n".join(content) + "\n", encoding="utf-8")
print("Generated 25-entry register, licence audit and upstream notices")
