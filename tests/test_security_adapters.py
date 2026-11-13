import copy
import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from integrations.base import ExecutionError, safe_run
from integrations.evidence_oscal import TrestleAdapter, canonical_json, sign_statement, statement, validate_oscal, verify_envelope
from integrations.runtime_security import OpaAdapter, PresidioAdapter
from conftest import login


def catalog():
    return {'catalog': {'uuid': str(uuid4()), 'metadata': {'title': 'Application-owned test controls',
                         'last-modified': '2026-11-13T00:00:00Z', 'version': '1.0.0', 'oscal-version': '1.2.1'},
                         'controls': [{'id': 'uag-test', 'title': 'Evidence review'}]}}


@pytest.fixture
def key_file(tmp_path):
    path = tmp_path / 'test-signing.pem'
    key = Ed25519PrivateKey.generate()
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return str(path)


def test_real_trestle_accepts_valid_and_rejects_invalid_oscal():
    assert importlib.metadata.version('compliance-trestle') == '5.2.1'
    document = catalog()
    assert validate_oscal(document)['valid'] is True
    result = TrestleAdapter().execute({'document': document}, {})
    assert result.status == 'succeeded'
    assert result.raw_output == document
    assert result.provenance['sha256'] == hashlib.sha256(canonical_json(document)).hexdigest()
    del document['catalog']['metadata']
    invalid = TrestleAdapter().execute({'document': document}, {})
    assert invalid.status == 'failed'
    assert invalid.error['code'] == 'invalid_oscal'


def test_trestle_does_not_accept_non_oscal_or_unknown_fields():
    assert TrestleAdapter().execute({'document': {'a': 1}}, {}).status == 'failed'
    value = catalog()
    value['catalog']['invented'] = True
    assert TrestleAdapter().execute({'document': value}, {}).status == 'failed'


def test_real_dsse_signing_verification_and_tampering(key_file, tmp_path):
    digest = hashlib.sha256(b'test evidence').hexdigest()
    value = statement('evidence-id', digest, {'tenant_id': 'tenant-one'})
    envelope = sign_statement(value, key_file)
    assert verify_envelope(envelope, key_file, digest, 'evidence-id')['valid']
    assert not verify_envelope(envelope, key_file, '0'*64, 'evidence-id')['valid']
    assert not verify_envelope(envelope, key_file, digest, 'different-id')['valid']
    changed = copy.deepcopy(envelope)
    changed['payload'] = changed['payload'][:-4] + 'AAAA'
    assert not verify_envelope(changed, key_file, digest)['valid']
    assert not verify_envelope(envelope, str(tmp_path / 'missing.pem'), digest)['valid']
    assert 'PRIVATE KEY' not in json.dumps(envelope)


def test_subprocess_limits_and_cancel(tmp_path):
    result = safe_run([str(Path(sys.executable).resolve()), '-c', 'print("bounded")'], cwd=tmp_path)
    assert result.stdout.strip() == 'bounded'
    assert result.returncode == 0
    with pytest.raises(ExecutionError, match='output_limit_exceeded'):
        safe_run([str(Path(sys.executable).resolve()), '-c', 'print("x"*10000)'], cwd=tmp_path, max_output=100)
    with pytest.raises(ExecutionError, match='timeout'):
        safe_run([str(Path(sys.executable).resolve()), '-c', 'import time; time.sleep(10)'], cwd=tmp_path, timeout=.1)
    with pytest.raises(ExecutionError, match='cancelled'):
        safe_run([str(Path(sys.executable).resolve()), '-c', 'print("unused")'], cwd=tmp_path, cancelled=lambda: True)
    with pytest.raises(ValueError, match='absolute'):
        safe_run(['python', '-c', 'pass'], cwd=tmp_path)


def test_network_adapters_do_not_accept_tenant_urls(monkeypatch):
    for adapter in (OpaAdapter(), PresidioAdapter()):
        with pytest.raises(ValueError): adapter.validate_config({'url': 'http://169.254.169.254'})
    monkeypatch.delenv('OPA_URL', raising=False)
    assert OpaAdapter().health({})['status'] == 'Not configured'
    result = OpaAdapter().execute({'risk_level': 'minimal'}, {'error_action': 'review'})
    assert result.status == 'failed' and result.normalized['action'] == 'review'
    monkeypatch.delenv('PRESIDIO_ANALYZER_URL', raising=False)
    result = PresidioAdapter().execute({'text': 'no stored prompt'}, {'error_action': 'block'})
    assert result.status == 'failed' and result.normalized['action'] == 'block'
    assert 'no stored prompt' not in result.model_dump_json()


def test_presidio_rejects_malformed_response_in_isolated_unit_test(monkeypatch):
    # A mock is used only to exercise hostile response parsing, not connectivity.
    import integrations.runtime_security
    monkeypatch.setattr(integrations.runtime_security, 'request_json', lambda *args, **kwargs: [
        {'start': 0, 'end': 2, 'entity_type': 'EMAIL_ADDRESS', 'score': float('nan')}])
    result = PresidioAdapter().execute({'text': 'test'}, {})
    assert result.status == 'failed'
    assert result.normalized['action'] == 'block'


@pytest.mark.skipif(not os.environ.get('TEST_OPA_URL'), reason='real OPA service not configured; no mock substituted')
def test_real_opa_pinned_policy(monkeypatch):
    monkeypatch.setenv('OPA_URL', os.environ['TEST_OPA_URL'])
    adapter = OpaAdapter()
    assert adapter.health({})['status'] == 'Connected'
    cases = [({}, 'review'),
             ({'risk_level': 'minimal', 'contains_pii': False}, 'allow'),
             ({'risk_level': 'unacceptable'}, 'block'),
             ({'risk_level': 'minimal', 'contains_pii': True}, 'block'),
             ({'risk_level': 'high', 'contains_pii': False}, 'review'),
             ({'risk_level': 'high', 'contains_pii': False, 'approved': True}, 'allow')]
    for value, expected in cases:
        result = adapter.execute(value, {})
        assert result.status == 'succeeded', result
        assert result.normalized['action'] == expected


def test_evidence_sign_download_verify_and_isolation(client, headers, key_file, monkeypatch):
    import uag.evidence
    monkeypatch.setattr(uag.evidence, 'settings', SimpleNamespace(signing_key_path=key_file))
    response = client.post('/api/v1/evidence', headers=headers, json={'title': 'Test report', 'content': '  Exact evidence\nbytes\n'})
    assert response.status_code == 201, response.text
    evidence = response.json()
    identifier = evidence['id']
    assert 'content' not in evidence
    assert evidence['sha256'] == hashlib.sha256(b'  Exact evidence\nbytes\n').hexdigest()
    assert client.get(f'/api/v1/evidence/{identifier}/download', headers=headers).content == b'  Exact evidence\nbytes\n'
    before = client.get(f'/api/v1/evidence/{identifier}/verify', headers=headers).json()
    assert before['integrity_valid'] and not before['signed'] and not before['signature_valid']
    signed = client.post(f'/api/v1/evidence/{identifier}/attest', headers=headers)
    assert signed.status_code == 201, signed.text
    after = client.get(f'/api/v1/evidence/{identifier}/verify', headers=headers).json()
    assert after['integrity_valid'] and after['signature_valid']
    other_headers = login(client, 'admin2@test.invalid', 'tenant-2')
    assert client.get(f'/api/v1/evidence/{identifier}/download', headers=other_headers).status_code == 404
    assert client.post(f'/api/v1/evidence/{identifier}/attest', headers=other_headers).status_code == 404
    assert client.get('/api/v1/evidence', headers=other_headers).json() == []
    package = client.get('/api/v1/evidence/export', headers=headers)
    assert package.status_code == 200 and package.headers['content-type'] == 'application/zip'


def test_evidence_rejects_xml_entity_and_invalid_oscal(client, headers):
    response = client.post('/api/v1/evidence', headers=headers, json={'title': 'Invalid', 'content': '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>', 'media_type': 'application/xml'})
    assert response.status_code == 422
    response = client.post('/api/v1/evidence', headers=headers, json={'title': 'Invalid JSON', 'content': '{"value":NaN}', 'media_type': 'application/json'})
    assert response.status_code == 422
    response = client.post('/api/v1/evidence', headers=headers, json={'title': 'Invalid OSCAL', 'content': '{"catalog":{}}', 'media_type': 'application/json'})
    assert response.status_code == 422
