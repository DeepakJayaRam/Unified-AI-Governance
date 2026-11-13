"""Catalogue contains every investigated entry; execution needs a registered adapter."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def catalog():
    records = []
    packaged = Path(__file__).parent / "catalog.json"
    source_sets = []
    for filename in ("governance.json", "security.json"):
        path = ROOT / "docs" / "research" / filename
        if path.exists():
            source_sets.extend(json.loads(path.read_text(encoding="utf-8-sig")))
    if not source_sets and packaged.exists():
        source_sets = json.loads(packaged.read_text(encoding="utf-8"))
    for source in source_sets:
        item = dict(source)
        item["id"] = str(item.get("slug", item["id"]))
        item["description"] = item.get("description", item.get("capabilities", ""))
        if isinstance(item["description"], list):
            item["description"] = "; ".join(item["description"])
        item["source_url"] = item.get("source_url", item.get("official_source_url", ""))
        records.append(item)
    return sorted(records, key=lambda item: item.get("number", 0))


def adapters():
    # Each module exists only after source/interface verification.
    from importlib import import_module
    combined = {}
    for name in ("discovery", "evidence_oscal", "runtime_security"):
        try:
            combined.update(import_module("integrations." + name).ADAPTERS)
        except ModuleNotFoundError as exc:
            if exc.name != "integrations." + name:
                raise
    return combined
