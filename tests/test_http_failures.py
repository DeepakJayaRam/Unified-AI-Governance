"""Real loopback HTTP fault injection; not an upstream-service success claim."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from integrations.runtime_security import OpaAdapter, PresidioAdapter


@pytest.fixture
def fault_service():
    state = {'mode': 'malformed'}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if state['mode'] == 'timeout':
                time.sleep(3.5)
            if state['mode'] == 'failure':
                self.send_response(503)
                self.end_headers()
                return
            if self.path == '/analyze':
                value = [{'start': 0, 'end': 5, 'entity_type': 'PERSON', 'score': .9}]
                if state['mode'] == 'malformed':
                    value[0]['end'] = 999999
            elif self.path == '/anonymize':
                value = {'text': '[REDACTED] alice@example.invalid'}
            else:
                value = {'result': {'action': 'unexpected'}}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps(value).encode())
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', state
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('mode', ['malformed', 'failure', 'timeout', 'restored_text'])
def test_presidio_http_faults_fail_closed_without_prompt_echo(monkeypatch, fault_service, mode):
    origin, state = fault_service
    state['mode'] = mode
    monkeypatch.setenv('PRESIDIO_ANALYZER_URL', origin)
    monkeypatch.setenv('PRESIDIO_ANONYMIZER_URL', origin)
    started = time.monotonic()
    result = PresidioAdapter().execute({'text': 'Alice [REDACTED_EMAIL]'}, {'error_action': 'review'})
    assert result.status == 'failed' and result.normalized['action'] == 'review'
    assert result.normalized.get('sanitized_text') is None
    assert 'Alice' not in result.model_dump_json()
    assert 'alice@example.invalid' not in result.model_dump_json()
    assert time.monotonic() - started < 5


def test_opa_http_malformed_and_service_failure(monkeypatch, fault_service):
    origin, state = fault_service
    monkeypatch.setenv('OPA_URL', origin)
    for mode in ('malformed', 'failure'):
        state['mode'] = mode
        result = OpaAdapter().execute({'risk_level': 'minimal'}, {})
        assert result.status == 'failed' and result.normalized['action'] == 'block'
