"""Verified OSCAL models and an application-owned in-toto/DSSE implementation."""
from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .base import AdapterResult

PAYLOAD_TYPE = 'application/vnd.in-toto+json'
STATEMENT_TYPE = 'https://in-toto.io/Statement/v1'
PREDICATE_TYPE = 'https://deepakjayaram.github.io/unified-ai-governance-security/predicates/evidence/v1'
OSCAL_MODELS = {'catalog': 'catalog', 'profile': 'profile',
                'component-definition': 'component', 'system-security-plan': 'ssp',
                'assessment-plan': 'assessment_plan', 'assessment-results': 'assessment_results',
                'plan-of-action-and-milestones': 'poam'}


def canonical_json(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def bounded_json(value: dict, limit=2_000_000):
    if not isinstance(value, dict) or len(canonical_json(value)) > limit:
        raise ValueError('JSON document must be an object smaller than 2 MB')
    def depth(item, level=0):
        if level > 40:
            raise ValueError('JSON nesting exceeds 40 levels')
        if isinstance(item, dict):
            for child in item.values(): depth(child, level+1)
        elif isinstance(item, list):
            for child in item: depth(child, level+1)
    depth(value)


def validate_oscal(document: dict) -> dict:
    bounded_json(document)
    if len(document) != 1 or next(iter(document)) not in OSCAL_MODELS:
        raise ValueError('Supported OSCAL root required: ' + ', '.join(OSCAL_MODELS))
    root = next(iter(document))
    model = importlib.import_module('trestle.oscal.' + OSCAL_MODELS[root]).Model
    model.model_validate(document)
    return {'valid': True, 'format': 'OSCAL JSON', 'model': root,
            'oscal_version': document[root].get('metadata', {}).get('oscal-version'),
            'validator': 'compliance-trestle', 'validator_version': importlib.metadata.version('compliance-trestle')}


class TrestleAdapter:
    id = 'compliance-trestle'
    version = '5.2.1'
    capabilities = ['validate_oscal_json']

    def validate_config(self, config):
        if config: raise ValueError('Trestle validator accepts no configuration')
        return {}

    def health(self, config):
        self.validate_config(config)
        try:
            actual = importlib.metadata.version('compliance-trestle')
            return {'status': 'Connected' if actual == self.version else 'Failed', 'detail': 'compliance-trestle ' + actual}
        except importlib.metadata.PackageNotFoundError:
            return {'status': 'Not configured', 'detail': 'Install pinned compliance-trestle package'}

    def execute(self, input, config, cancelled=lambda: False):
        self.validate_config(config)
        if cancelled(): return AdapterResult(status='failed', error={'code': 'cancelled'})
        document = input.get('document')
        try:
            result = validate_oscal(document)
            return AdapterResult(status='succeeded', raw_output=document, normalized=result,
                                 provenance={'tool': self.id, 'version': importlib.metadata.version('compliance-trestle'),
                                             'sha256': hashlib.sha256(canonical_json(document)).hexdigest()},
                                 logs=['Validated JSON using upstream Trestle model; no references fetched'])
        except (ValueError, TypeError, RecursionError, ImportError, ValidationError) as exc:
            return AdapterResult(status='failed', raw_output=document,
                                 error={'code': 'invalid_oscal', 'detail': type(exc).__name__},
                                 logs=['OSCAL schema validation failed; content omitted from logs'])


class Subject(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=512)
    digest: dict[str, str]


def statement(name: str, digest: str, predicate: dict) -> dict:
    if len(digest) != 64 or any(ch not in '0123456789abcdef' for ch in digest):
        raise ValueError('A lowercase SHA-256 digest is required')
    Subject(name=name, digest={'sha256': digest})
    bounded_json(predicate)
    return {'_type': STATEMENT_TYPE, 'subject': [{'name': name, 'digest': {'sha256': digest}}],
            'predicateType': PREDICATE_TYPE, 'predicate': predicate}


def pae(payload_type: str, payload: bytes) -> bytes:
    encoded_type = payload_type.encode('utf-8')
    return b'DSSEv1 ' + str(len(encoded_type)).encode() + b' ' + encoded_type + b' ' + str(len(payload)).encode() + b' ' + payload


def signing_key(path: str) -> Ed25519PrivateKey:
    if not path:
        raise ValueError('Signing key is not configured')
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError('Configured signing key must be Ed25519')
    return key


def key_id(key) -> str:
    return hashlib.sha256(key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).hexdigest()


def sign_statement(value: dict, path: str) -> dict:
    key = signing_key(path)
    payload = canonical_json(value)
    return {'payloadType': PAYLOAD_TYPE, 'payload': base64.b64encode(payload).decode('ascii'),
            'signatures': [{'keyid': key_id(key), 'sig': base64.b64encode(key.sign(pae(PAYLOAD_TYPE, payload))).decode('ascii')}]}


def verify_envelope(envelope: dict, path: str, expected_digest: str, expected_name: str | None = None, trusted_keys_dir: str = '') -> dict:
    """Verify against deployment-configured trust, never an envelope-supplied key."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        trusted = {}
        if path:
            key = signing_key(path)
            trusted[key_id(key)] = key.public_key()
        if trusted_keys_dir:
            files=list(Path(trusted_keys_dir).glob('*.pub'))
            if len(files)>100: raise ValueError('Too many trusted public keys')
            for file in files:
                if file.is_symlink() or file.stat().st_size>8192:
                    raise ValueError('Invalid public key file')
                public_key=serialization.load_pem_public_key(file.read_bytes())
                if not isinstance(public_key,Ed25519PublicKey): raise ValueError('Ed25519 public key required')
                fingerprint=hashlib.sha256(public_key.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).hexdigest()
                trusted[fingerprint]=public_key
        if set(envelope) != {'payloadType', 'payload', 'signatures'} or envelope['payloadType'] != PAYLOAD_TYPE:
            raise ValueError('Invalid envelope')
        payload = base64.b64decode(envelope['payload'], validate=True)
        if len(payload) > 2_000_000 or len(envelope['signatures']) != 1:
            raise ValueError('Invalid envelope size or signatures')
        signature = envelope['signatures'][0]
        public_key=trusted.get(signature['keyid'])
        if public_key is None: raise ValueError('Untrusted signing key')
        public_key.verify(base64.b64decode(signature['sig'], validate=True), pae(PAYLOAD_TYPE, payload))
        decoded = json.loads(payload)
        if decoded['_type'] != STATEMENT_TYPE or decoded['predicateType'] != PREDICATE_TYPE:
            raise ValueError('Unexpected statement/predicate')
        subjects = decoded['subject']
        if len(subjects) != 1 or subjects[0]['digest'] != {'sha256': expected_digest}:
            raise ValueError('Subject digest does not match evidence')
        if expected_name is not None and subjects[0]['name'] != expected_name:
            raise ValueError('Subject identity does not match evidence')
        return {'valid': True, 'key_id': signature['keyid'], 'algorithm': 'Ed25519', 'statement': decoded}
    except (ValueError, TypeError, KeyError, OSError, InvalidSignature, json.JSONDecodeError):
        return {'valid': False, 'reason': 'Signature, trusted key or evidence binding verification failed'}


class InTotoAdapter:
    id = 'in-toto'
    version = 'Statement v1 / application predicate v1'
    capabilities = ['generate_unsigned_statement']

    def validate_config(self, config):
        if config: raise ValueError('Statement generator accepts no configuration')
        return {}

    def health(self, config):
        self.validate_config(config)
        return {'status': 'Connected', 'detail': 'Local Statement v1 generator; signing is a separate evidence operation'}

    def execute(self, input, config, cancelled=lambda: False):
        self.validate_config(config)
        try:
            if cancelled(): raise ValueError('cancelled')
            result = statement(input['name'], input['sha256'], input.get('predicate', {}))
            return AdapterResult(status='succeeded', raw_output=result,
                                 normalized={'statement': result, 'signed': False},
                                 provenance={'tool': self.id, 'version': self.version},
                                 logs=['Created unsigned in-toto Statement v1; no authenticity claim'])
        except (KeyError, ValueError, TypeError):
            return AdapterResult(status='failed', error={'code': 'invalid_statement_input'})


ADAPTERS = {adapter.id: adapter for adapter in (TrestleAdapter(), InTotoAdapter())}
