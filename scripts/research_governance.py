"""Read-only upstream inspection. Stores metadata and hashes, not copied source."""
import concurrent.futures, hashlib, json, pathlib, subprocess, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOS = {
    1: 'cdxgen/cdxgen', 2: 'GenAI-Security-Project/aibom-generator',
    3: 'opencomplai/opencomplai', 4: 'aiexponent/riskforge',
    5: 'AbdelStark/eu-ai-act-toolkit', 6: 'Venturalitica/venturalitica-sdk',
    7: 'compl-ai/compl-ai', 8: 'morganrcu/awesome-eu-ai-act',
    9: 'Ankit-Uniyal/iso-42001-ai-governance-toolkit',
    10: 'Ankit-Uniyal/eu-ai-act-compliance-toolkit', 11: 'IBM/ai-atlas-nexus',
}
FILES = ['README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'pyproject.toml', 'package.json', 'requirements.txt', 'setup.py', 'Dockerfile']

def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'UAG-research/0.1'}), timeout=25) as response:
            data = response.read(150000)
            return {'url':url, 'status':response.status, 'sha256':hashlib.sha256(data).hexdigest(), 'text':data.decode(errors='replace')}
    except Exception as error:
        return {'url':url, 'error':str(error)}

def inspect(item):
    number, repo = item
    ls = subprocess.run(['git','ls-remote',f'https://github.com/{repo}','HEAD','refs/tags/*'],capture_output=True,text=True,timeout=40)
    rows = ls.stdout.splitlines()
    commit = next((row.split()[0] for row in rows if row.endswith('\tHEAD')), None)
    record = {'number':number, 'repository':repo, 'inspected_at':'2026-11-13', 'commit':commit, 'refs':rows[-20:], 'error':ls.stderr.strip() or None}
    if commit:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            record['files'] = list(pool.map(fetch,[f'https://raw.githubusercontent.com/{repo}/{commit}/{path}' for path in FILES]))
    return record

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = list(pool.map(inspect, REPOS.items()))
    # Temporary raw material is ignored by Git; curated records cite these URLs.
    destination = ROOT/'tmp'/'governance-research.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(records,indent=2),encoding='utf-8')
    for record in records:
        print(record['number'],record['repository'],record['commit'])
        for file in record.get('files',[]):
            if 'text' in file:
                print(file['url'].rsplit('/',1)[-1],len(file['text']))
