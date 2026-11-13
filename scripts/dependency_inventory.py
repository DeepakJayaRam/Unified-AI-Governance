"""Record installed distribution versions/licence metadata without vendoring code."""
import importlib.metadata
import json
from pathlib import Path

rows = []
for distribution in importlib.metadata.distributions():
    meta = distribution.metadata
    if meta.get('Name', '').lower() == 'unified-ai-governance-security':
        continue
    license_text = meta.get('License-Expression') or meta.get('License') or 'See upstream package licence'
    if len(license_text) > 300:
        license_text = 'Full licence text is included in installed package; see upstream notice'
    rows.append({'name':meta['Name'],'version':distribution.version,'licence_metadata':license_text,
                 'project_urls':meta.get_all('Project-URL') or []})
target=Path('docs/dependency-inventory.json')
target.write_text(json.dumps(sorted(rows,key=lambda item:item['name'].lower()),indent=2),encoding='utf-8')
print(f'Recorded {len(rows)} installed Python distributions; npm inventories are package-lock.json files')
