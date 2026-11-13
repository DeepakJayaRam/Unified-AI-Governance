"""Security and persistence regressions. Service doubles here are parser/pipeline unit tests."""
import json
from concurrent.futures import ThreadPoolExecutor

from conftest import login
from integrations.base import AdapterResult
from uag.db import Record, SessionLocal

API = '/api/v1'


def create(client, headers, path, body):
    response = client.post(API + path, headers=headers, json=body)
    assert response.status_code in {200, 201, 202}, response.text
    return response.json()


def test_membership_changes_and_last_administrator(client, headers):
    member = create(client, headers, '/memberships', {'email':'contributor@test.invalid','name':'Contributor','password':'Testing-password-2026!','role':'contributor'})
    contributor = login(client, 'contributor@test.invalid')
    assert client.post(API+'/systems',headers=contributor,json={'name':'Permitted contribution'}).status_code == 201
    assert client.patch(API+'/memberships/user-1',headers=contributor,json={'role':'viewer'}).status_code == 403
    assert client.delete(API+'/memberships/user-1',headers=headers).status_code == 409
    assert client.patch(API+'/memberships/user-1',headers=headers,json={'role':'viewer'}).status_code == 409
    assert client.patch(API+'/memberships/'+member['id'],headers=headers,json={'role':'viewer'}).status_code == 200
    assert client.post(API+'/systems',headers=contributor,json={'name':'Denied'}).status_code == 403
    assert client.delete(API+'/memberships/'+member['id'],headers=headers).status_code == 204
    assert client.get(API+'/systems',headers=contributor).status_code == 403


def test_password_change_revokes_every_session(client, headers):
    second_session = login(client)
    assert client.post(API+'/auth/password',headers=headers,json={'current_password':'incorrect','new_password':'New-password-2026!'}).status_code == 403
    assert client.post(API+'/auth/password',headers=headers,json={'current_password':'Testing-password-2026!','new_password':'New-password-2026!'}).status_code == 204
    for session in (headers, second_session):
        assert client.get(API+'/auth/me',headers=session).status_code == 401
    assert client.post(API+'/auth/login',json={'email':'admin1@test.invalid','password':'Testing-password-2026!'}).status_code == 401
    assert client.post(API+'/auth/login',json={'email':'admin1@test.invalid','password':'New-password-2026!'}).status_code == 200


def test_resource_pagination_idempotency_and_stale_edits(client, headers):
    keyed = {**headers, 'Idempotency-Key':'system-create-001'}
    first = create(client,keyed,'/systems',{'name':'Original'})
    assert create(client,keyed,'/systems',{'name':'Original'})['id'] == first['id']
    assert client.post(API+'/systems',headers=keyed,json={'name':'Different'}).status_code == 409
    for name in ('Second','Third'):
        create(client,headers,'/systems',{'name':name})
    a=client.get(API+'/systems?limit=2',headers=headers)
    b=client.get(API+'/systems?limit=2&offset=2',headers=headers)
    assert a.headers['X-Total-Count'] == '3'
    assert len(a.json()) == 2 and len(b.json()) == 1
    assert {r['id'] for r in a.json()}.isdisjoint({r['id'] for r in b.json()})
    edited=client.patch(API+'/systems/'+first['id'],headers={**headers,'If-Match':'1'},json={'name':'Updated'})
    assert edited.status_code == 200 and edited.json()['version'] == 2
    assert client.patch(API+'/systems/'+first['id'],headers={**headers,'If-Match':'1'},json={'name':'Lost update'}).status_code == 409
    assert client.get(API+'/systems?limit=501',headers=headers).status_code == 422


def test_three_framework_records_and_traceability(client, headers):
    system=create(client,headers,'/systems',{'name':'Governed system'})
    evidence=create(client,headers,'/evidence',{'title':'Review minutes','content':'Synthetic minutes'})
    for framework, kind in [('eu_ai_act','classification'),('iso42001','management_review'),('nist_ai_rmf','risk_treatment')]:
        assessment=create(client,headers,'/assessments',{'name':'Review','framework':framework,'system_id':system['id']})
        payload={'title':'Decision record','framework':framework,'kind':kind,'system_id':system['id'],'assessment_id':assessment['id'],'evidence_ids':[evidence['id']],'due_date':'2026-12-01','rationale':'Human documented rationale','source_url':'https://example.org/source','source_version':'2026'}
        record=create(client,headers,'/governance-records',payload)
        assert client.patch(API+'/governance-records/'+record['id'],headers={**headers,'If-Match':'1'},json={**payload,'status':'approved'}).status_code == 200
        assert client.patch(API+'/governance-records/'+record['id'],headers={**headers,'If-Match':'1'},json=payload).status_code == 409
        assert client.post(API+'/governance-records',headers=headers,json={**payload,'due_date':'not-a-date'}).status_code == 422
        foreign=login(client,'admin2@test.invalid','tenant-2')
        assert client.patch(API+'/governance-records/'+record['id'],headers=foreign,json=payload).status_code == 404
        control=assessment['controls'][0]['id']
        assert client.put(API+f"/assessments/{assessment['id']}/controls/{control}",headers=headers,json={'status':'implemented','evidence_ids':[evidence['id']]}).status_code == 200
        history=client.get(API+f"/assessments/{assessment['id']}/history",headers=headers).json()
        assert len(history)==1 and history[0]['snapshot']['controls'][0]['status']=='not_started'
        exported=client.get(API+f"/assessments/{assessment['id']}/export",headers=headers)
        assert exported.status_code==200 and exported.json()['framework_source'].startswith('https://')
    assert len(client.get(API+'/frameworks/crosswalks',headers=headers).json())==4


def test_governance_rejects_cross_framework_and_contributor_approval(client,headers):
    system=create(client,headers,'/systems',{'name':'System'})
    assessment=create(client,headers,'/assessments',{'name':'EU','system_id':system['id'],'framework':'eu_ai_act'})
    body={'framework':'nist_ai_rmf','kind':'risk_treatment','title':'Risk treatment','system_id':system['id'],'assessment_id':assessment['id']}
    assert client.post(API+'/governance-records',headers=headers,json=body).status_code==422
    create(client,headers,'/memberships',{'name':'Contributor','email':'contributor@test.invalid','password':'Testing-password-2026!','role':'contributor'})
    contributor=login(client,'contributor@test.invalid')
    assert client.post(API+'/governance-records',headers=contributor,json={**body,'framework':'eu_ai_act','status':'approved'}).status_code==403


def test_policy_history_review_resolution_and_no_prompt_retention(client,headers):
    policy=create(client,headers,'/policies',{'name':'Review PII','config':{'pii_action':'review'}})
    result=create(client,headers,'/guardrails/evaluate',{'policy_id':policy['id'],'text':'Synthetic alice@example.invalid','direction':'output'})
    assert result['decision']=='review' and result['sanitized_text'] is None
    reviews=client.get(API+'/runtime/reviews',headers=headers).json()
    assert len(reviews)==1 and reviews[0]['status']=='pending'
    foreign=login(client,'admin2@test.invalid','tenant-2')
    assert client.patch(API+'/runtime/reviews/'+reviews[0]['id'],headers=foreign,json={'resolution':'allow','notes':'Approved'}).status_code==404
    resolved=client.patch(API+'/runtime/reviews/'+reviews[0]['id'],headers=headers,json={'resolution':'block','notes':'Requires redaction'})
    assert resolved.status_code==200
    assert client.patch(API+'/runtime/reviews/'+reviews[0]['id'],headers=headers,json={'resolution':'allow','notes':'Too late'}).status_code==409
    update=client.patch(API+'/policies/'+policy['id'],headers={**headers,'If-Match':'1'},json={'name':'Block PII','config':{'pii_action':'block'}})
    assert update.status_code==200 and update.json()['version']==2
    restored=create(client,headers,f"/policies/{policy['id']}/rollback",{'revision':1})
    assert restored['version']==3 and restored['config']['pii_action']=='review'
    assert len(client.get(API+f"/policies/{policy['id']}/versions",headers=headers).json())==2
    with SessionLocal() as db:
        rows=db.query(Record).filter(Record.kind.in_(['runtime_events','runtime_reviews'])).all()
        assert 'alice@example.invalid' not in json.dumps([r.data for r in rows])


def test_runtime_disabled_service_uses_explicit_error_action(client,headers):
    policy=create(client,headers,'/policies',{'name':'External','config':{'checks':['presidio'],'error_action':'review'}})
    result=create(client,headers,'/guardrails/evaluate',{'policy_id':policy['id'],'text':'Synthetic safe text'})
    assert result['decision']=='review'
    assert result['checks'][0]['status']=='not_configured'


def test_composed_sanitizers_cannot_restore_native_redactions(client,headers,monkeypatch):
    from integrations.runtime_security import ADAPTERS
    assert client.put(API+'/integrations/presidio/config',headers=headers,json={'enabled':True,'config':{}}).status_code==200
    received=[]
    def execute(payload,config):
        received.append(payload['text'])
        return AdapterResult(status='succeeded',normalized={'action':'sanitize','sanitized_text':payload['text'].replace('Alice','[PERSON]'),'entities':[{'entity_type':'PERSON'}]})
    monkeypatch.setattr(ADAPTERS['presidio'],'execute',execute)
    policy=create(client,headers,'/policies',{'name':'Composed','config':{'checks':['native','presidio'],'pii_action':'sanitize'}})
    result=create(client,headers,'/guardrails/evaluate',{'policy_id':policy['id'],'text':'Alice alice@example.invalid'})
    assert received==['Alice [REDACTED_EMAIL]']
    assert result['sanitized_text']=='[PERSON] [REDACTED_EMAIL]'


def test_five_tenants_concurrent_reads_are_isolated(client,headers):
    # SQLite exercise of concurrent API reads; production RLS is tested separately.
    sessions=[headers,login(client,'admin2@test.invalid','tenant-2')]
    for n in range(3):
        tenant=create(client,headers,'/tenants',{'name':f'Client {n+3}'})
        sessions.append({**headers,'X-Tenant-ID':tenant['id']})
    systems=[create(client,h,'/systems',{'name':f'Private system {n}'}) for n,h in enumerate(sessions)]
    def read(pair):
        index,h=pair
        own=client.get(API+'/systems',headers=h)
        assert [r['id'] for r in own.json()]==[systems[index]['id']]
        for other in systems:
            response=client.get(API+'/systems/'+other['id'],headers=h)
            assert response.status_code==(200 if other==systems[index] else 404)
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(read,enumerate(sessions)))


def test_repeated_policy_save_preserves_distinct_history(client,headers):
    payload={'name':'Stable policy','config':{'pii_action':'block'}}
    policy=create(client,headers,'/policies',payload)
    for version in (2,3):
        response=client.patch(API+'/policies/'+policy['id'],headers=headers,json=payload)
        assert response.status_code==200 and response.json()['version']==version
    assert len(client.get(API+f"/policies/{policy['id']}/versions",headers=headers).json())==2


def test_public_trust_store_verifies_after_private_key_rotation(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from integrations.evidence_oscal import sign_statement,statement,verify_envelope
    import hashlib
    digest=hashlib.sha256(b'evidence').hexdigest()
    old=Ed25519PrivateKey.generate()
    private=tmp_path/'old.pem'
    private.write_bytes(old.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    envelope=sign_statement(statement('evidence',digest,{}),str(private))
    public=tmp_path/'trusted';public.mkdir()
    (public/'old.pub').write_bytes(old.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
    assert verify_envelope(envelope,'',digest,'evidence',str(public))['valid']
    assert not verify_envelope(envelope,'',digest,'another-subject',str(public))['valid']
    assert not verify_envelope(envelope,'','0'*64,'evidence',str(public))['valid']
    (public/'old.pub').unlink()
    assert not verify_envelope(envelope,'',digest,'evidence',str(public))['valid']
