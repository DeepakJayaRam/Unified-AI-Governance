"""Real deployment restart, RLS, Redis rate-limit and worker recovery checks.

Only the named UAG Compose project is controlled. Never removes a volume.
Uses synthetic records; abandoned-worker timestamps are explicitly injected.
"""
import json
import os
import secrets
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','-f','docker-compose.yml','-f','docker-compose.presidio.yml','-f','docker-compose.signing.yml']
report={'status':'failed','tests':{},'scope':'Actual UAG Compose services and synthetic tenant; no unrelated services or volumes modified'}


def command(*args):
    result=subprocess.run(COMPOSE+list(args),cwd=ROOT,capture_output=True,text=True,timeout=180)
    assert result.returncode==0, result.stderr[-1000:]
    return result.stdout


def inside(code, payload):
    return json.loads(command('exec','-T','api','python','-c',code,json.dumps(payload)))


def main():
    suffix=secrets.token_hex(6)
    credentials=json.loads((ROOT/os.getenv('UAG_RELEASE_CREDENTIALS','tmp/release-browser-credentials.json')).read_text())
    client=httpx.Client(base_url='http://127.0.0.1:8100/api/v1',timeout=30)
    def call(path,body=None,method='POST',expected=(200,201,202)):
        response=client.request(method,path,json=body)
        assert response.status_code in expected, f'{path}: {response.status_code}'
        return response.json() if response.content else None
    identity=call('/auth/login',credentials)
    client.headers.update({'Authorization':'Bearer '+identity['access_token'],'X-Tenant-ID':identity['memberships'][0]['tenant_id']})
    tenant=call('/tenants',{'name':'Recovery verification '+suffix})
    client.headers['X-Tenant-ID']=tenant['id']
    system=call('/systems',{'name':'Persistent synthetic system','risk_level':'minimal'})
    evidence=call('/evidence',{'title':'Persistent evidence','content':'Synthetic recovery evidence','system_id':system['id']})
    call('/evidence/'+evidence['id']+'/attest',{})
    for tool in ('opa','cdxgen','presidio'):
        call('/integrations/'+tool+'/config',{'enabled':True,'config':{}},method='PUT')
    sql_result=inside('''
import json,sys
from sqlalchemy import text
from uag.db import SessionLocal,set_tenant
p=json.loads(sys.argv[1]); result={}
with SessionLocal() as db:
 result['role']=dict(db.execute(text('SELECT current_user AS name,rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user')).mappings().one())
 assert not result['role']['rolsuper'] and not result['role']['rolbypassrls']
 assert db.scalar(text('SELECT count(*) FROM records'))==0
 result['unscoped_records']=0
 result['migration']=db.scalar(text('SELECT version_num FROM alembic_version'))
 assert result['migration']=='0002'
 set_tenant(db,p['tenant'])
 assert db.scalar(text('SELECT count(*) FROM records WHERE id=:id'),{'id':p['system']})==1
 assert db.scalar(text('SELECT count(*) FROM records WHERE tenant_id<>:tenant'),{'tenant':p['tenant']})==0
 result['foreign_rows']=0
print(json.dumps(result))
''',{'tenant':tenant['id'],'system':system['id']})
    report['tests']['deployed_postgres_role_rls_migration']=sql_result
    # Exhaust one isolated identity through actual HTTP. Another identity must
    # still work; the deployment's quota is deliberately shared across tenants
    # belonging to the same identity.
    members=[]
    for i in range(2):
        body={'email':f'ratetest-{suffix}-{i}@test.invalid','name':'Rate verification','password':secrets.token_urlsafe(30),'role':'viewer'}
        call('/memberships',body)
        auth=call('/auth/login',{'email':body['email'],'password':body['password']})
        members.append({'Authorization':'Bearer '+auth['access_token'],'X-Tenant-ID':tenant['id']})
    with httpx.Client(base_url=str(client.base_url),timeout=30) as requests:
        def read(_):return requests.get('/systems',headers=members[0]).status_code
        with ThreadPoolExecutor(max_workers=12) as pool:
            counts=Counter(pool.map(read,range(620)))
        assert counts=={200:600,429:20},counts
        assert requests.get('/systems',headers=members[1]).status_code==200
    report['tests']['real_http_atomic_identity_rate_limit']={'statuses':dict(counts),'independent_identity':200,'limit':'600 per 60 seconds per identity across its tenants'}
    print('RLS and concurrent rate limit passed',flush=True)
    command('stop','worker')
    try:
        payload={'integration_id':'opa','system_id':system['id'],'input':{'risk_level':'minimal','contains_pii':False}}
        queued=call('/executions',payload)
        cancelled=call('/executions',payload)
        assert call('/executions/'+cancelled['id']+'/cancel',{})['status']=='cancelled'
        retried=call('/executions/'+cancelled['id']+'/retry',{})
        stale=call('/executions',payload)
        redis_key='uag:release:'+suffix
        injected=inside('''
import json,sys,os
from datetime import timedelta
from redis import Redis
from uag.db import SessionLocal,Record,set_tenant,now
p=json.loads(sys.argv[1]);redis=Redis.from_url(os.environ['REDIS_URL'])
redis.set(p['key'],'persistent',ex=1800)
# Delete only the exact synthetic pointer to test DB reconciliation.
removed=redis.lrem('uag:jobs',0,json.dumps({'tenant_id':p['tenant'],'job_id':p['queued']}))
assert removed==1
with SessionLocal() as db:
 set_tenant(db,p['tenant']); row=db.get(Record,p['stale'])
 row.data={**row.data,'status':'running'};row.updated_at=now()-timedelta(minutes=11);db.commit()
print(json.dumps({'lost_notification':removed,'stale_lease':'synthetic running state; expiry advanced 11 minutes'}))
''',{'tenant':tenant['id'],'queued':queued['id'],'stale':stale['id'],'key':redis_key})
        report['tests']['recovery_fault_setup']=injected
        command('restart','postgres','redis','opa','presidio','api','frontend')
        command('up','-d','--wait','api','frontend','opa','presidio','worker')
        for identifier in (queued['id'],retried['id']):
            for _ in range(60):
                job=call('/executions/'+identifier,method='GET')
                if job['status'] not in ('queued','running'):break
                time.sleep(1)
            assert job['status']=='succeeded',job.get('error')
        assert call('/executions/'+cancelled['id'],method='GET')['status']=='cancelled'
        abandoned=call('/executions/'+stale['id'],method='GET')
        assert abandoned['status']=='failed' and abandoned['error']['code']=='worker_interrupted'
        recovered=call('/executions/'+stale['id']+'/retry',{})
        for _ in range(60):
            job=call('/executions/'+recovered['id'],method='GET')
            if job['status'] not in ('queued','running'):break
            time.sleep(1)
        assert job['status']=='succeeded'
        assert call('/systems/'+system['id'],method='GET')['name']=='Persistent synthetic system'
        checked=call('/evidence/'+evidence['id']+'/verify',method='GET')
        assert checked['integrity_valid'] and checked['signature_valid']
        assert inside('import json,os,sys;from redis import Redis;p=json.loads(sys.argv[1]);print(json.dumps(Redis.from_url(os.environ["REDIS_URL"]).get(p["key"]).decode()))',{'key':redis_key})=='persistent'
        assert call('/audit/verify',method='GET')['valid']
        report['tests']['restart_persistence_signatures_redis_audit']='passed'
        report['tests']['queued_reconciliation_cancel_retry_and_expired_lease']='passed'
    finally:
        command('start','worker')
    report['status']='passed'
    print('Persistence and worker recovery passed',flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        report['error']=str(exc)
        raise
    finally:
        (ROOT/'docs/release/recovery.json').write_text(json.dumps(report,indent=2)+'\n')
