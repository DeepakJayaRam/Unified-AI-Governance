"""Exercise the real Compose API/Redis worker and five isolated synthetic tenants.

Requires a running stack with Presidio and signing overlays. Test credentials
are loaded from an ignored file; no credentials or access tokens are reported.
"""
import json
import os
import platform
import secrets
import subprocess
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
from benchmark import distribution

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW_ONLY='--workflow-only' in sys.argv
REPORT=ROOT/'docs/release'/('compose-workflow-v0.2.json' if WORKFLOW_ONLY else 'compose-verification.json')
report={'scope':'Actual Compose API, PostgreSQL, Redis worker, OPA and Presidio; synthetic tenants only','tests':{},'benchmarks':{},'status':'failed','environment':{'client':platform.platform(),'cpu':platform.processor(),'logical_cpus':os.cpu_count()}}


def main():
    credentials=json.loads((ROOT/os.getenv('UAG_RELEASE_CREDENTIALS','tmp/release-browser-credentials.json')).read_text(encoding='utf-8'))
    client=httpx.Client(base_url='http://127.0.0.1:8100/api/v1',timeout=30)
    response=client.post('/auth/login',json=credentials)
    assert response.status_code==200,'Release identity login failed'
    identity=response.json()
    client.headers.update({'Authorization':'Bearer '+identity['access_token'],'X-Tenant-ID':identity['memberships'][0]['tenant_id']})

    def request(path,body=None,method='POST',expected=(200,201,202),headers=None):
        response=client.request(method,path,json=body,headers=headers)
        assert response.status_code in expected,f'{method} {path} returned {response.status_code}'
        return response.json() if response.content else None

    suffix=secrets.token_hex(5)
    systems=[]; tenants=[]
    for index in range(5):
        tenant=request('/tenants',{'name':f'Release client {suffix}-{index}'})
        tenant_headers={'X-Tenant-ID':tenant['id']}
        tenants.append(tenant_headers)
        system=request('/systems',{'name':f'Private system {index}','risk_level':'minimal'},headers=tenant_headers)
        systems.append(system)
        request('/evidence',{'title':'Private original','content':'Synthetic evidence','system_id':system['id']},headers=tenant_headers)

    def isolated(index):
        scoped=tenants[index]
        for path in ['/systems','/evidence']:
            rows=request(path,method='GET',headers=scoped)
            assert len(rows)==1
        for other in range(5):
            request('/systems/'+systems[other]['id'],method='GET',headers=scoped,expected=(200,) if other==index else (404,))
        return True
    with ThreadPoolExecutor(max_workers=5) as pool:
        assert all(pool.map(isolated,range(5)))
    report['tests']['five_tenant_concurrent_api_isolation']='passed'

    system=request('/systems',{'name':'Release workflow '+suffix,'risk_level':'minimal'})
    evidence=request('/evidence',{'title':'Signed original '+suffix,'content':'  Synthetic release evidence\n','system_id':system['id']})
    request(f"/evidence/{evidence['id']}/attest",{})
    verified=request(f"/evidence/{evidence['id']}/verify",method='GET')
    assert verified['integrity_valid'] and verified['signature_valid']
    original=client.get(f"/evidence/{evidence['id']}/download")
    assert original.content==b'  Synthetic release evidence\n'
    assert client.get('/evidence/export').status_code==200
    report['tests']['evidence_sign_verify_original_download_package']='passed'

    for framework,kind in [('eu_ai_act','classification'),('iso42001','management_review'),('nist_ai_rmf','risk_treatment')]:
        assessment=request('/assessments',{'name':'Release assessment','system_id':system['id'],'framework':framework})
        request(f"/assessments/{assessment['id']}/controls/{assessment['controls'][0]['id']}",{'status':'implemented','evidence_ids':[evidence['id']],'owner':'Synthetic reviewer'},method='PUT')
        risk=request('/risks',{'title':'Risk treatment needed','system_id':system['id'],'owner':'Synthetic reviewer'})
        request('/governance-records',{'framework':framework,'kind':kind,'title':'Documented governance decision','system_id':system['id'],'assessment_id':assessment['id'],'risk_id':risk['id'],'evidence_ids':[evidence['id']],'rationale':'Synthetic release verification','owner':'Synthetic reviewer'})
        assert len(request(f"/assessments/{assessment['id']}/history",method='GET'))==1
        assert request(f"/assessments/{assessment['id']}/export",method='GET')['assessment']['id']==assessment['id']
    report['tests']['three_framework_assessment_history_evidence_and_records']='passed'

    for tool in ['cdxgen','opa','presidio','compliance-trestle','in-toto']:
        # Catalogue identifiers are asserted so changes cannot silently select a different tool.
        catalog=request('/integrations',method='GET')
        assert any(item['id']==tool for item in catalog),tool
        request(f'/integrations/{tool}/config',{'enabled':True,'config':{}},method='PUT')
        health=request(f'/integrations/{tool}/health',{})
        assert health['status'] in ['Connected','Available'],f'{tool} health: {health}'
        report['tests'][tool+'_health']=health

    bom_input={'package_json':{'name':'release-app','version':'1.0.0','dependencies':{'openai':'6.8.1'}},'package_lock':{'name':'release-app','version':'1.0.0','lockfileVersion':3,'packages':{'':{'name':'release-app','version':'1.0.0','dependencies':{'openai':'6.8.1'}},'node_modules/openai':{'version':'6.8.1','license':'Apache-2.0'}}}}
    idem='release-'+suffix
    def submit(_):
        return request('/executions',{'integration_id':'cdxgen','system_id':system['id'],'input':bom_input},headers={'Idempotency-Key':idem})['id']
    with ThreadPoolExecutor(max_workers=5) as pool:
        ids=list(pool.map(submit,range(5)))
    assert len(set(ids))==1
    for _ in range(150):
        job=request('/executions/'+ids[0],method='GET')
        if job['status'] not in {'queued','running'}: break
        time.sleep(1)
    assert job['status']=='succeeded',job.get('error')
    assert job.get('provenance') and job.get('raw_output')
    report['tests']['redis_worker_real_cdxgen_and_concurrent_idempotency']={'status':'passed','job_id':job['id'],'provenance':job['provenance']}
    boms=request('/bom',method='GET')
    bom=next(row for row in boms if row.get('execution_id')==job['id'])
    assert request(f"/bom/{bom['id']}/export",method='GET')['bomFormat']=='CycloneDX'

    cases=[] if WORKFLOW_ONLY else [('native',['native'],'Contact alice@example.invalid','sanitize'),('presidio',['presidio'],'Contact alice@example.com','sanitize'),('opa',['opa'],'Synthetic safe text','allow'),('pipeline',['native','presidio','opa'],'Synthetic safe text','allow')]
    for name,checks,text,expected in cases:
        policy=request('/policies',{'name':'Release '+name,'config':{'checks':checks,'pii_action':'sanitize','error_action':'block'}})
        durations=[]; component_times=[]
        for sample in range(105):
            started=time.perf_counter()
            result=request('/guardrails/evaluate',{'policy_id':policy['id'],'system_id':system['id'],'text':text})
            elapsed=(time.perf_counter()-started)*1000
            assert result['decision']==expected,f'{name}: {result}'
            assert all(c['status']=='executed' for c in result['checks'])
            if sample>=5:
                durations.append(elapsed);component_times.append(result['latency_ms'])
        report['benchmarks'][name]={'http_roundtrip':distribution(durations),'pipeline_before_persistence':distribution(component_times),'sample_size':100,'warmup':5,'includes':'Bearer auth, membership, Redis rate limit, PostgreSQL RLS, selected checks, audit/event persistence, loopback HTTP; excludes external ingress'}
    assert request('/audit/verify',method='GET')['valid']
    assert request('/reports/export',method='GET')['resources']['governance_records']
    report['tests']['audit_chain_and_report']='passed'
    report['status']='passed'


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        report['error']=str(exc)
        raise
    finally:
        REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'status':report['status'],'checks':len(report['tests']),'report':str(REPORT.relative_to(ROOT))}))
