"""Isolated authenticated HTTP benchmark. Do not run browser tests concurrently."""
import json
import os
import platform
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from benchmark import distribution

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = {'status': 'interrupted', 'started_at': datetime.now(timezone.utc).isoformat(),
              'environment': {'client': platform.platform(), 'cpu': platform.processor(),
                              'logical_cpus': os.cpu_count(), 'deployment': 'Docker Compose Linux containers; loopback ports 8100/3100; host OS recorded in client; unrelated services are not controlled'},
              'includes': 'HTTP roundtrip, bearer authentication, membership, Redis rate limiting, PostgreSQL RLS, selected controls, runtime event and audit persistence',
              'excludes': 'TLS, public ingress, WAN, cloud hardware; pacing is outside timed samples',
              'execution': 'Sequential isolated benchmark; dedicated identity, no browser suite; 5 warmups and 100 measured samples per case',
              'cases': {}}
    destination = ROOT/'docs/release/benchmark-v0.2.json'
    try:
        credentials = json.loads((ROOT/os.getenv('UAG_RELEASE_CREDENTIALS','tmp/release-browser-credentials.json')).read_text())
        with httpx.Client(base_url='http://127.0.0.1:8100/api/v1', timeout=30) as client:
            assert client.get('http://127.0.0.1:8100/health').status_code == 200
            def call(path, body):
                response = client.post(path, json=body)
                assert response.status_code in (200, 201, 202), f'{path}: HTTP {response.status_code}'
                return response.json()
            identity = call('/auth/login', credentials)
            client.headers.update({'Authorization': 'Bearer '+identity['access_token'], 'X-Tenant-ID': identity['memberships'][0]['tenant_id']})
            suffix = secrets.token_hex(6)
            password = secrets.token_urlsafe(30)
            email = f'benchmark-{suffix}@test.invalid'
            call('/memberships', {'email': email, 'name': 'Isolated release benchmark', 'password': password, 'role': 'organisation_admin'})
            dedicated = call('/auth/login', {'email': email, 'password': password})
            client.headers['Authorization'] = 'Bearer '+dedicated['access_token']
            system = call('/systems', {'name': 'Benchmark '+suffix, 'risk_level': 'minimal'})
            for tool in ('opa','presidio'):
                response = client.put(f'/integrations/{tool}/config', json={'enabled':True,'config':{}})
                assert response.status_code == 200
                assert call(f'/integrations/{tool}/health', {})['status'] == 'Connected'
            inputs = {'short_safe': 'A plain synthetic message.', 'short_pii': 'Contact alice@example.com.',
                      'near_limit': ('plain text ' * 3000)[:31975]+' alice@example.com'}
            for pipeline, checks in [('native',['native']), ('complete',['native','presidio','opa'])]:
                policy = call('/policies', {'name':f'Benchmark {pipeline} {suffix}', 'config':{'checks':checks,'pii_action':'sanitize','error_action':'block'}})
                for name, text in inputs.items():
                    durations, control_times = [], []
                    expected = 'allow' if name == 'short_safe' else ('sanitize' if pipeline == 'native' else 'block')
                    for sample in range(105):
                        started = time.perf_counter()
                        result = call('/guardrails/evaluate', {'policy_id':policy['id'],'system_id':system['id'],'text':text})
                        elapsed = (time.perf_counter()-started)*1000
                        assert result['decision'] == expected, f'{pipeline}/{name}: {result["decision"]}'
                        assert all(check['status']=='executed' for check in result['checks'])
                        if sample >= 5:
                            durations.append(elapsed)
                            control_times.append(result['latency_ms'])
                        # Stay below the actual 600/minute identity limit, without
                        # changing deployment settings or silently retrying 429s.
                        time.sleep(max(0, .13 - (time.perf_counter()-started)))
                    report['cases'][f'{pipeline}/{name}'] = {'input_characters':len(text), 'decision':expected,
                        'http':distribution(durations), 'controls_before_persistence':distribution(control_times)}
                    destination.write_text(json.dumps(report,indent=2)+'\n')
                    print(pipeline, name, json.dumps(report['cases'][f'{pipeline}/{name}']['http']), flush=True)
            report['status']='passed'
    except Exception as exc:
        report['error']=str(exc)
        raise
    finally:
        destination.write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
