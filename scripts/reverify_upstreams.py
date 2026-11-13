"""Recheck the supplied 25-entry catalogue against live official sources."""
import base64
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib.request
import urllib.error
from github_inspect import read, session_token

token=session_token()
root=Path(__file__).resolve().parents[1]
entries=json.loads((root/'integrations/catalog.json').read_text(encoding='utf-8'))


def check(entry):
    url=entry['source_url']
    result={'number':entry['number'],'id':entry['id'],'source_url':url,'previous_classification':entry['classification']}
    try:
        if url.startswith('https://github.com/'):
            repo='/'.join(url.split('/')[3:5])
            metadata=read('/repos/'+repo,token)
            result.update({'canonical_repository':metadata['html_url'],'archived':metadata['archived'],'default_branch':metadata['default_branch'],'updated_at':metadata['updated_at'],'licence_spdx':(metadata.get('license') or {}).get('spdx_id')})
            result['head_commit']=read('/repos/'+repo+'/commits/'+metadata['default_branch'],token)['sha']
            try:
                result['latest_release']=read('/repos/'+repo+'/releases/latest',token)['tag_name']
            except urllib.error.HTTPError as exc:
                result['latest_release_status']=exc.code
            try:
                licence=read('/repos/'+repo+'/license',token)
                content=base64.b64decode(licence['content'])
                result['licence_sha256']=hashlib.sha256(content).hexdigest()
                result['licence_source']=licence['html_url']
                result['licence_first_line']=content.decode('utf-8',errors='replace').strip().splitlines()[0][:200]
            except urllib.error.HTTPError as exc:
                result['licence_status']=exc.code
        else:
            request=urllib.request.Request(url,headers={'User-Agent':'UAG-source-verification'})
            with urllib.request.urlopen(request,timeout=30) as response:
                content=response.read(4_000_000)
                result.update({'http_status':response.status,'content_sha256':hashlib.sha256(content).hexdigest(),'final_url':response.url})
        result['verification_status']='source_rechecked'
    except Exception as exc:
        result.update({'verification_status':'unavailable','error_type':type(exc).__name__,'http_status':getattr(exc,'code',None)})
    return result


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(check,entries))
    target=root/'docs/release/upstream-reverification.json'
    target.parent.mkdir(exist_ok=True,parents=True)
    target.write_text(json.dumps(results,indent=2),encoding='utf-8')
    for item in results:
        print(item['number'],item['id'],item['verification_status'],item.get('latest_release'),item.get('licence_spdx'))
