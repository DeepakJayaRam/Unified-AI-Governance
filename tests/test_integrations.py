import hashlib
from integrations.registry import adapters, catalog
from test_api_workflows import API, post
from conftest import login


def test_complete_catalogue_and_honest_execution_states(client, headers):
    entries = catalog()
    assert len(entries) == 25
    assert {r['number'] for r in entries} == set(range(1, 26))
    assert len({r['id'] for r in entries}) == 25
    states = client.get(API + '/integrations', headers=headers).json()
    for entry in states:
        if entry['classification'] in {'REFERENCE_RESOURCE', 'DEFERRED', 'BLOCKED_BY_LICENCE'}:
            assert client.post(API + '/executions', headers=headers, json={'integration_id':entry['id'], 'input':{}}).status_code == 409
    assert next(row for row in states if row['id'] == 'verifywise')['status'] == 'Licence restricted'


def test_integrity_preserves_whitespace_and_audit_chain(client, headers):
    content = '  original evidence\n\n'
    evidence = post(client, headers, '/evidence', {'title':'Exact bytes', 'content':content})
    assert evidence['sha256'] == hashlib.sha256(content.encode()).hexdigest()
    response = client.get(API + f"/evidence/{evidence['id']}/download", headers=headers)
    assert response.text == content
    assert client.get(API + '/audit/verify', headers=headers).json()['valid']


def test_execution_tenant_scope_and_no_credential_config(client, headers):
    from uag.db import Record, SessionLocal
    with SessionLocal() as db:
        db.add(Record(id='other-job', tenant_id='tenant-2', kind='executions', data={'status':'queued'}))
        db.commit()
    assert client.get(API + '/executions/other-job', headers=headers).status_code == 404
    assert client.post(API + '/executions/other-job/cancel', headers=headers).status_code == 404
    # Executables and URLs are deployment-controlled rather than tenant-controlled.
    response = client.put(API + '/integrations/cdxgen/config', headers=headers, json={'enabled':True, 'config':{'command':'echo unsafe'}})
    assert response.status_code == 422
