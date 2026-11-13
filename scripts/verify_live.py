"""Real HTTP workflow + latency checks in an isolated synthetic workspace."""
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark import distribution


def main():
    workspace = ROOT / 'tmp' / ('live-' + secrets.token_hex(4))
    workspace.mkdir(parents=True)
    env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + (workspace/'live.db').as_posix(), 'EXECUTION_MODE':'local', 'SIGNING_KEY_PATH':str(workspace/'signing.pem'), 'TEMP':str(workspace),'TMP':str(workspace)}
    password = secrets.token_urlsafe(24)
    env['UAG_BOOTSTRAP_PASSWORD'] = password
    commands = [
        [sys.executable,'-m','alembic','upgrade','head'],
        [sys.executable,'-m','uag.cli','bootstrap','--email','benchmark@test.invalid','--tenant','Isolated synthetic validation'],
        [sys.executable,'-m','uag.cli','keygen','--path',env['SIGNING_KEY_PATH']],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        if result.returncode: raise RuntimeError(result.stderr)
    log = (workspace/'server.log').open('w')
    server = subprocess.Popen([sys.executable,'-m','uvicorn','uag.main:app','--host','127.0.0.1','--port','8102','--no-access-log'],cwd=ROOT,env=env,stdout=log,stderr=log)
    report = {'environment':'Windows Python 3.14, loopback HTTP, SQLite, one uvicorn process; synthetic records only', 'tests':{},'benchmarks':{}}
    try:
        with httpx.Client(base_url='http://127.0.0.1:8102',timeout=120) as client:
            for _ in range(50):
                try:
                    if client.get('/health').is_success: break
                except httpx.ConnectError: pass
                time.sleep(.2)
            response = client.post('/api/v1/auth/login',json={'email':'benchmark@test.invalid','password':password})
            response.raise_for_status()
            identity = response.json()
            client.headers.update({'Authorization':'Bearer '+identity['access_token'],'X-Tenant-ID':identity['memberships'][0]['tenant_id']})
            def create(path, body):
                response = client.post('/api/v1'+path,json=body)
                response.raise_for_status()
                return response.json()
            system = create('/systems',{'name':'Synthetic HTTP validation'})
            evidence = create('/evidence',{'system_id':system['id'],'title':'Synthetic evidence','content':'  Validation artefact\n'})
            create('/evidence/'+evidence['id']+'/attest',{})
            check = client.get('/api/v1/evidence/'+evidence['id']+'/verify').json()
            assert check['integrity_valid'] and check['signature_valid']
            report['tests']['evidence_sign_verify'] = 'passed'
            assessment = create('/assessments',{'system_id':system['id'],'name':'Synthetic assessment','framework':'nist_ai_rmf'})
            response = client.put('/api/v1/assessments/'+assessment['id']+'/controls/MEASURE',json={'status':'implemented','evidence_ids':[evidence['id']]})
            response.raise_for_status()
            report['tests']['assessment_evidence_attachment'] = 'passed'
            policy = create('/policies',{'name':'Synthetic runtime benchmark','config':{'pii_action':'sanitize','blocked_terms':['forbidden'],'error_action':'block'}})
            for name, text in {'short_pii':'Contact person@example.invalid','max_input':'A'*31960+' person@example.invalid'}.items():
                durations = []
                for i in range(210):
                    start=time.perf_counter()
                    result=create('/guardrails/evaluate',{'policy_id':policy['id'],'text':text})
                    duration=(time.perf_counter()-start)*1000
                    assert result['decision']=='sanitize'
                    if i>=10: durations.append(duration)
                report['benchmarks'][name]=distribution(durations)
            body={'package_json':{'name':'validation-app','version':'1.0.0','dependencies':{'openai':'6.8.1'}},'package_lock':{'name':'validation-app','version':'1.0.0','lockfileVersion':3,'packages':{'':{'name':'validation-app','version':'1.0.0','dependencies':{'openai':'6.8.1'}},'node_modules/openai':{'version':'6.8.1','license':'Apache-2.0'}}}}
            response=client.put('/api/v1/integrations/cdxgen/config',json={'enabled':True,'config':{}})
            response.raise_for_status()
            job=create('/executions',{'integration_id':'cdxgen','system_id':system['id'],'input':body})
            for _ in range(200):
                result=client.get('/api/v1/executions/'+job['id']).json()
                if result['status'] not in {'queued','running'}:break
                time.sleep(.2)
            assert result['status']=='succeeded', result.get('error')
            report['tests']['queued_cdxgen_scan']={'status':'passed','provenance':result.get('provenance'),'component_count':result.get('normalized',{}).get('component_count')}
            assert client.get('/api/v1/bom').json()
            assert client.get('/api/v1/audit/verify').json()['valid']
            report['tests']['audit_chain']='passed'
            exported=client.get('/api/v1/reports/export')
            exported.raise_for_status()
            report['tests']['report_export']='passed'
    finally:
        server.terminate()
        server.wait(timeout=10)
        log.close()
    target=ROOT/'docs/validation/http-workflow-benchmark.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
