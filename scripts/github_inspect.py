"""Read GitHub state through the normal Git credential helper; never print credentials."""
import json
import os
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

TARGET = 'DeepakJayaRam/Unified-AI-Governance'


def session_token():
    result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n', text=True,
                            capture_output=True, timeout=30, env={**os.environ, 'GCM_INTERACTIVE':'never', 'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:
        return None
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    return fields.get('password')


def read(path, token=None):
    headers = {'User-Agent':'Unified-AI-Governance-release-audit', 'Accept':'application/vnd.github+json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request('https://api.github.com' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    token = session_token()
    result = {'repository': 'https://github.com/' + TARGET, 'credential_available': bool(token)}
    try:
        if token:
            result['authenticated_login'] = read('/user', token)['login']
        repo = read('/repos/' + TARGET, token)
        result.update({'public': not repo['private'], 'default_branch':repo['default_branch'], 'permissions':repo.get('permissions', {})})
        result['branches'] = [{'name': b['name'], 'sha':b['commit']['sha'], 'protected':b['protected']} for b in read('/repos/' + TARGET + '/branches', token)]
        runs = read('/repos/' + TARGET + '/actions/runs?per_page=5', token)['workflow_runs']
        result['ci_runs'] = [{'id':r['id'], 'sha':r['head_sha'], 'status':r['status'], 'conclusion':r['conclusion'], 'url':r['html_url']} for r in runs]
    except urllib.error.HTTPError as exc:
        result['api_error_status'] = exc.code
    target = Path('docs/release/github-inspection.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
