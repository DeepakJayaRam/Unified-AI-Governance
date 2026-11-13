"""Opt-in actual Presidio service tests. No HTTP or recognizer mocks."""
import os
import httpx
import pytest
from integrations.runtime_security import PresidioAdapter

pytestmark=pytest.mark.skipif(not os.getenv('TEST_PRESIDIO_URL'),reason='Real Presidio service is not configured')


def test_real_presidio_detection_redaction_and_failure_policy(monkeypatch):
    origin=os.environ['TEST_PRESIDIO_URL']
    monkeypatch.setenv('PRESIDIO_ANALYZER_URL',origin)
    monkeypatch.setenv('PRESIDIO_ANONYMIZER_URL',origin)
    adapter=PresidioAdapter()
    assert adapter.health({})['status']=='Connected'
    result=adapter.execute({'text':'Contact alice@example.com for the synthetic test.'},{})
    assert result.status=='succeeded'
    assert result.normalized['action']=='sanitize'
    assert 'alice@example.com' not in result.model_dump_json()
    assert any(span['entity_type']=='EMAIL_ADDRESS' for span in result.normalized['entities'])
    failed=adapter.execute({'text':'Synthetic test'},{'language':'zz','error_action':'review'})
    assert failed.status=='failed' and failed.normalized['action']=='review'


def test_real_presidio_contract_rejects_untrusted_offsets_without_echo():
    origin=os.environ['TEST_PRESIDIO_URL']
    with httpx.Client(base_url=origin,trust_env=False,timeout=5) as client:
        health=client.get('/health').json()
        assert health['analyzer']==health['anonymizer']=='2.2.366'
        assert health['model']=='en_core_web_sm-3.8.0'
        response=client.post('/anonymize',json={'text':'SyntheticPrivateMarker','analyzer_results':[{'start':0,'end':999,'entity_type':'EMAIL_ADDRESS','score':1}],'anonymizers':{'DEFAULT':{'type':'replace','new_value':'[REDACTED]'}}})
        assert response.status_code==422
        assert 'SyntheticPrivateMarker' not in response.text
        response=client.post('/analyze',json={'text':'SyntheticPrivateMarker','language':'unsupported'})
        assert response.status_code==422 and 'SyntheticPrivateMarker' not in response.text


def test_real_presidio_preserves_prior_redactions(monkeypatch):
    origin = os.environ['TEST_PRESIDIO_URL']
    monkeypatch.setenv('PRESIDIO_ANALYZER_URL', origin)
    monkeypatch.setenv('PRESIDIO_ANONYMIZER_URL', origin)
    result = PresidioAdapter().execute({'text': 'Contact [REDACTED_EMAIL] or bob@example.com'}, {})
    assert result.status == 'succeeded'
    assert '[REDACTED_EMAIL]' in result.normalized['sanitized_text']
    assert 'bob@example.com' not in result.normalized['sanitized_text']
