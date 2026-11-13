import concurrent.futures,json,pathlib,re,urllib.request
from research_governance import fetch
root=pathlib.Path(__file__).resolve().parents[1]
records=json.loads((root/'tmp/governance-research.json').read_text(encoding='utf8'))
paths={1:['bin/cdxgen.js','lib/cli/options.js'],3:['packages/cli/pyproject.toml','docs/src/getting-started/scanner.md','docs/src/guides/ci-integration.md'],4:['docs/cli-reference.md'],5:['packages/sdk/package.json','packages/cli/package.json'],9:['15-SCRIPTS/ai_assessment_checker.py','15-SCRIPTS/aims_soa_tracker.py'],10:['CHANGELOG.md','scripts/README.md']}
for r in records:
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        r['files'].extend(pool.map(fetch,[f'https://raw.githubusercontent.com/{r["repository"]}/{r["commit"]}/{p}' for p in paths.get(r['number'],[])]))
(root/'tmp/governance-research.json').write_text(json.dumps(records,indent=2),encoding='utf8')
urls=['https://pypi.org/pypi/riskforge/json','https://pypi.org/pypi/opencomplai-cli/json','https://pypi.org/pypi/venturalitica/json','https://pypi.org/pypi/ai-atlas-nexus/json','https://registry.npmjs.org/@cdxgen%2fcdxgen/latest','https://registry.npmjs.org/@eu-ai-act%2fsdk/latest','https://registry.npmjs.org/@eu-ai-act%2fcli/latest','https://m3framework.org/','https://m3framework.org/license.html','https://airc.nist.gov/','https://eur-lex.europa.eu/eli/reg/2024/1689/oj','https://eur-lex.europa.eu/eli/reg/2026/1744/oj']
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    extras=list(pool.map(fetch,urls))
(root/'tmp/governance-extras.json').write_text(json.dumps(extras,indent=2),encoding='utf8')
for f in extras:
    if 'text' not in f: print(f['url'],f.get('error'));continue
    if 'json' in f['url'] or 'registry.' in f['url']:
        d=json.loads(f['text']); info=d.get('info',d)
        print(f['url'],info.get('version'),info.get('license'),info.get('engines'))
    else:
        print(f['url'],f['status'],f['sha256'])
        if 'm3framework' in f['url']: print(re.findall(r'https://github.com/[^\s\"<>]+',f['text'])[:8])
