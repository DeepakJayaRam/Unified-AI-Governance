"""Deployment-controlled HTTP adapters; tenant input cannot choose hosts or paths."""
import hashlib
import math
import os
import re
import time
from functools import lru_cache
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .base import AdapterResult
from .evidence_oscal import bounded_json, canonical_json


def endpoint(variable):
    value = os.environ.get(variable, '').rstrip('/')
    parsed = urlsplit(value)
    if not value or parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {'', '/'}:
        raise ValueError(variable + ' must be a deployment-configured HTTP(S) origin')
    return value


@lru_cache(maxsize=4)
def service_client(timeout):
    # HTTPX clients are thread-safe; pooled internal connections avoid rebuilding
    # TLS/proxy transports on every synchronous policy check. No tenant headers.
    return httpx.Client(timeout=httpx.Timeout(timeout),follow_redirects=False,trust_env=False,
                        limits=httpx.Limits(max_connections=16,max_keepalive_connections=16))


def request_json(variable, method, path, *, data=None, timeout=3, health=False):
    deadline=time.monotonic()+10
    headers = {}
    # Optional bearer credential is deployment-only and never returned/logged.
    token = os.environ.get(variable.replace('_URL', '_TOKEN'))
    if token: headers['Authorization'] = 'Bearer ' + token
    with service_client(timeout).stream(method, endpoint(variable) + path, json=data, headers=headers) as response:
        response.raise_for_status()
        raw = bytearray()
        for chunk in response.iter_bytes():
            if time.monotonic()>deadline:
                raise TimeoutError('Integration response deadline exceeded')
            raw.extend(chunk)
            if len(raw) > 1_000_000: raise ValueError('Integration response exceeds limit')
        if not raw or health: return {}
        import json
        return json.loads(raw)


class OpaConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    error_action: str = Field(default='block', pattern='^(block|review)$')


class OpaAdapter:
    id = 'opa'
    version = '1.22.4'
    capabilities = ['evaluate_pinned_policy']

    def validate_config(self, config): return OpaConfig.model_validate(config).model_dump()

    def health(self, config):
        self.validate_config(config)
        try:
            request_json('OPA_URL', 'GET', '/health')
            return {'status': 'Connected', 'detail': 'OPA HTTP health passed; deployment must pin 1.22.4'}
        except ValueError:
            return {'status': 'Not configured', 'detail': 'Configure deployment OPA_URL'}
        except Exception:
            return {'status': 'Failed', 'detail': 'OPA health check failed'}

    def execute(self, input, config, cancelled=lambda: False):
        config = self.validate_config(config)
        started = time.perf_counter()
        try:
            bounded_json(input, 100_000)
            if cancelled(): raise ValueError('cancelled')
            result = request_json('OPA_URL', 'POST', '/v1/data/uag/decision', data={'input': input})
            decision = result.get('result')
            if not isinstance(decision, dict) or decision.get('action') not in {'allow', 'block', 'review', 'sanitize'}:
                raise ValueError('OPA decision missing or malformed')
            return AdapterResult(status='succeeded', raw_output=result,
                                 normalized={**decision, 'latency_ms': round((time.perf_counter()-started)*1000, 3)},
                                 provenance={'tool': self.id, 'configured_version': self.version,
                                             'policy': 'uag/decision', 'input_sha256': hashlib.sha256(canonical_json(input)).hexdigest()},
                                 logs=['Evaluated pinned server-managed policy'])
        except Exception as exc:
            return AdapterResult(status='failed', normalized={'action': config['error_action'], 'latency_ms': round((time.perf_counter()-started)*1000, 3)},
                                 error={'code': 'policy_evaluation_unavailable', 'detail': type(exc).__name__},
                                 logs=['Explicit error action applied; no request content logged'])


class PresidioConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    language: str = Field(default='en', pattern='^[a-z]{2}$')
    score_threshold: float = Field(default=0.5, ge=0, le=1)
    action: str = Field(default='sanitize', pattern='^(allow|block|sanitize|review)$')
    error_action: str = Field(default='block', pattern='^(block|review)$')


class PresidioAdapter:
    id = 'presidio'
    version = '2.2.366'
    capabilities = ['detect_pii', 'anonymize_text']

    def validate_config(self, config): return PresidioConfig.model_validate(config).model_dump()

    def health(self, config):
        self.validate_config(config)
        try:
            request_json('PRESIDIO_ANALYZER_URL', 'GET', '/health', health=True)
            request_json('PRESIDIO_ANONYMIZER_URL', 'GET', '/health', health=True)
            return {'status': 'Connected', 'detail': 'Analyzer and anonymizer health passed; model coverage is deployment-specific'}
        except ValueError:
            return {'status': 'Not configured', 'detail': 'Configure deployment Presidio origins'}
        except Exception:
            return {'status': 'Failed', 'detail': 'Presidio health check failed'}

    def execute(self, input, config, cancelled=lambda: False):
        config = self.validate_config(config)
        started = time.perf_counter()
        try:
            text = input['text']
            if not isinstance(text, str) or not 1 <= len(text) <= 32000: raise ValueError('Invalid text length')
            if cancelled(): raise ValueError('cancelled')
            spans = request_json('PRESIDIO_ANALYZER_URL', 'POST', '/analyze', data={'text': text, 'language': config['language'], 'score_threshold': config['score_threshold']})
            if not isinstance(spans, list) or len(spans) > 10000: raise ValueError('Invalid analyzer response')
            clean = []
            for span in spans:
                if not isinstance(span, dict) or type(span.get('start')) is not int or type(span.get('end')) is not int or not 0 <= span['start'] < span['end'] <= len(text):
                    raise ValueError('Invalid analyzer offsets')
                if not isinstance(span.get('entity_type'), str) or not 1 <= len(span['entity_type']) <= 200:
                    raise ValueError('Invalid analyzer entity type')
                if type(span.get('score')) not in (int, float) or not math.isfinite(span['score']) or not 0 <= span['score'] <= 1:
                    raise ValueError('Invalid analyzer score')
                clean.append({key: span[key] for key in ('start', 'end', 'entity_type', 'score')})
            action = config['action'] if spans else 'allow'
            output = None
            if action == 'sanitize':
                anonymized = request_json('PRESIDIO_ANONYMIZER_URL', 'POST', '/anonymize', data={'text': text, 'analyzer_results': clean, 'anonymizers': {'DEFAULT': {'type': 'replace', 'new_value': '[REDACTED]'}}})
                output = anonymized['text']
                if not isinstance(output, str) or len(output) > 64000: raise ValueError('Invalid anonymizer result')
                # Accept only replacements of detected ranges. A malformed service
                # must not insert text or restore content removed by earlier checks.
                ranges = []
                for span in sorted(clean, key=lambda item: (item['start'], item['end'])):
                    if ranges and span['start'] <= ranges[-1][1]:
                        ranges[-1][1] = max(ranges[-1][1], span['end'])
                    else:
                        ranges.append([span['start'], span['end']])
                pieces, cursor = [], 0
                for start, end in ranges:
                    pieces.extend([re.escape(text[cursor:start]), r'(?:\[REDACTED\])+'])
                    cursor = end
                pieces.append(re.escape(text[cursor:]))
                if re.fullmatch(''.join(pieces), output) is None:
                    raise ValueError('Anonymizer changed text outside validated redactions')
            return AdapterResult(status='succeeded', raw_output={'analyzer_results': clean},
                                 normalized={'action': action, 'entities': clean, 'sanitized_text': output,
                                             'latency_ms': round((time.perf_counter()-started)*1000, 3)},
                                 provenance={'tool': self.id, 'configured_version': self.version,
                                             'language': config['language'], 'input_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'recognizer_coverage': 'deployment-configured'},
                                 logs=['Prompt text omitted from raw output and logs'])
        except Exception as exc:
            return AdapterResult(status='failed', normalized={'action': config['error_action'], 'latency_ms': round((time.perf_counter()-started)*1000, 3)},
                                 error={'code': 'pii_evaluation_unavailable', 'detail': type(exc).__name__})


ADAPTERS = {adapter.id: adapter for adapter in (OpaAdapter(), PresidioAdapter())}
