import urllib.request,json,concurrent.futures,pathlib,subprocess,hashlib
OUT=pathlib.Path('docs/research/sources')
repos=['oscal-compass/compliance-trestle','sigstore/cosign','in-toto/attestation','connectsmartconsulting/aigrc','open-policy-agent/opa','open-policy-agent/opa-envoy-plugin','envoyproxy/envoy','IMDA-BTG/aiverify','bluewave-labs/verifywise','microsoft/presidio','NVIDIA/NeMo-Guardrails','meta-llama/PurpleLlama']
def get(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Unified-AI-Governance-Research'}),timeout=25) as r:return r.read().decode('utf8')
 except Exception as e:return 'FETCH_ERROR: '+str(e)
def run(repo):
 ref=subprocess.run(['git','ls-remote','--symref','https://github.com/'+repo+'.git','HEAD'],capture_output=True,text=True,timeout=35)
 lines=ref.stdout.strip().splitlines();sha=lines[-1].split()[0] if lines else None
 result={'repo':repo,'git_reference':ref.stdout,'git_error':ref.stderr,'inspected_commit':sha,'sources':{}}
 if sha:
  for name in ['README.md','LICENSE','LICENSE.md','LICENSE.txt','pyproject.toml','package.json']:
   url='https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+name
   data=get(url)
   if not data.startswith('FETCH_ERROR'):result['sources'][name]={'url':url,'sha256':hashlib.sha256(data.encode()).hexdigest(),'bytes':len(data.encode()),'inspected_on':'2026-11-13'}
 p=OUT/(repo.replace('/','__')+'.json');p.write_text(json.dumps(result,indent=2),encoding='utf8')
 return repo,sha,list(result['sources'])
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for r in ex.map(run,repos):print(r)
