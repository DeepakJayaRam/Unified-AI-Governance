"""Tenant-owned text artefacts, provenance and locally trusted DSSE signatures."""
import hashlib
import io
import json
import zipfile

from defusedxml import ElementTree
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from integrations.evidence_oscal import OSCAL_MODELS, canonical_json, sign_statement, statement, validate_oscal, verify_envelope
from .auth import context, require_write
from .config import settings
from .db import get_db, now
from .resources import audit, create_record, get_record, listed, public, page
from .schemas import EvidenceCreate, EvidenceResponse

router = APIRouter()


def metadata(record):
    value = public(record)
    value.pop('content', None)
    return value


@router.get('/evidence', response_model=list[EvidenceResponse])
def evidence_list(response:Response,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000),ctx=Depends(context), db: Session = Depends(get_db)):
    return [metadata(item) for item in page(db, ctx, 'evidence',response,limit,offset)]


@router.post('/evidence', status_code=201, response_model=EvidenceResponse)
def evidence_create(body: EvidenceCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    raw = body.content.encode('utf-8')
    if len(raw) > 2_000_000: raise HTTPException(413, 'Evidence exceeds 2 MB')
    validation = {'format': body.media_type, 'valid': True}
    try:
        if body.media_type == 'application/json':
            def reject_constant(_):
                raise ValueError('Non-finite values are not valid JSON')
            document = json.loads(body.content, parse_constant=reject_constant)
            if isinstance(document, dict) and any(root in document for root in OSCAL_MODELS):
                validation = validate_oscal(document)
        elif body.media_type == 'application/xml':
            ElementTree.fromstring(body.content)
            validation = {'format': 'XML', 'valid': True, 'oscal_validated': False}
    except Exception:
        raise HTTPException(422, 'Artefact format validation failed; supply valid content in the selected format')
    value = {**body.model_dump(), 'sha256': hashlib.sha256(raw).hexdigest(), 'size_bytes': len(raw),
             'validation': validation, 'provenance': {'actor_id': ctx['user_id'], 'collected_at': now().isoformat(),
                                                     'source': 'authenticated_text_upload', 'encoding': 'utf-8'}}
    return metadata(create_record(db, ctx, 'evidence', value))


@router.get('/evidence/export')
def evidence_export(ctx=Depends(context), db: Session = Depends(get_db)):
    records = listed(db, ctx, 'evidence')
    if sum(x.data.get('size_bytes', 0) for x in records) > 20_000_000:
        raise HTTPException(413, 'Export exceeds 20 MB; use individual evidence downloads')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json', canonical_json({'tenant_id': ctx['tenant_id'], 'evidence': [metadata(x) for x in records]}))
        for record in records:
            archive.writestr('evidence/' + record.id + '.txt', record.data['content'].encode('utf-8'))
        for attestation in listed(db, ctx, 'attestations'):
            archive.writestr('attestations/' + attestation.id + '.json', canonical_json(public(attestation)))
    audit(db, ctx, 'evidence.exported', ctx['tenant_id'], {'count': len(records)})
    db.commit()
    return Response(output.getvalue(), media_type='application/zip', headers={'Content-Disposition': 'attachment; filename="evidence-package.zip"'})


@router.get('/evidence/{identifier}/download')
def download(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
    item = get_record(db, ctx, 'evidence', identifier)
    audit(db, ctx, 'evidence.downloaded', item.id)
    db.commit()
    return Response(item.data['content'].encode('utf-8'), media_type=item.data['media_type'],
                    headers={'Content-Disposition': 'attachment; filename="' + item.id + '.txt"', 'Content-Security-Policy': "default-src 'none'; sandbox"})


@router.post('/evidence/{identifier}/attest', status_code=201)
def attest(identifier: str, ctx=Depends(require_write), db: Session = Depends(get_db)):
    item = get_record(db, ctx, 'evidence', identifier)
    digest = hashlib.sha256(item.data['content'].encode('utf-8')).hexdigest()
    if digest != item.data['sha256']: raise HTTPException(409, 'Evidence integrity check failed')
    value = statement(item.id, digest, {'tenant_id': ctx['tenant_id'], 'evidence_id': item.id,
                                      'actor_id': ctx['user_id'], 'issued_at': now().isoformat(),
                                      'media_type': item.data['media_type']})
    try:
        envelope = sign_statement(value, settings.signing_key_path)
    except (ValueError, OSError):
        raise HTTPException(503, 'Server signing key is unavailable; configure SIGNING_KEY_PATH')
    record = create_record(db, ctx, 'attestations', {'evidence_id': item.id, 'sha256': digest,
                                                   'envelope': envelope, 'algorithm': 'Ed25519',
                                                   'key_id': envelope['signatures'][0]['keyid']})
    return public(record)


@router.get('/evidence/{identifier}/verify')
def verify(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
    item = get_record(db, ctx, 'evidence', identifier)
    digest = hashlib.sha256(item.data['content'].encode('utf-8')).hexdigest()
    checks = []
    for record in listed(db, ctx, 'attestations'):
        if record.data.get('evidence_id') == item.id:
            check = verify_envelope(record.data['envelope'], settings.signing_key_path, digest, item.id, getattr(settings,'trusted_signing_keys_dir',''))
            check.pop('statement', None)
            checks.append({'attestation_id': record.id, **check})
    result = {'evidence_id': item.id, 'sha256': digest, 'integrity_valid': digest == item.data['sha256'],
              'signed': bool(checks), 'signatures': checks,
              'signature_valid': bool(checks) and all(check['valid'] for check in checks)}
    audit(db, ctx, 'evidence.verified', item.id, {'integrity_valid': result['integrity_valid'], 'signature_valid': result['signature_valid']})
    db.commit()
    return result
