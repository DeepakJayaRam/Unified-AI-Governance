import hashlib
import json
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import Response
from pydantic import ConfigDict, ValidationError, create_model
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .auth import context, require_admin, require_write
from .db import Audit, Record, get_db
from .frameworks import FRAMEWORKS, new_controls
from .resources import audit, create_record, get_record, listed, public, references, page, lock_tenant
from .schemas import AssessmentCreate, BomCreate, ControlUpdate, RiskCreate, SettingsUpdate, SystemCreate

router = APIRouter()


def resource_routes(kind, schema):
    response_schema = create_model(kind.title() + "Record", __base__=schema, __config__=ConfigDict(extra="allow"), id=(str, ...), created_at=(str, ...), updated_at=(str, ...))
    def list_items(response: Response, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0, le=1000000), ctx=Depends(context), db: Session = Depends(get_db)):
        return [public(r) for r in page(db, ctx, kind, response, limit, offset)]
    def create_item(body: schema, idempotency_key: str | None=Header(None, min_length=8, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$'), ctx=Depends(require_write), db: Session = Depends(get_db)):
        lock_tenant(db, ctx)
        key = 'request:'+idempotency_key if idempotency_key else None
        if key:
            previous = db.scalar(select(Record).where(Record.tenant_id==ctx['tenant_id'], Record.kind==kind, Record.resource_key==key))
            if previous:
                if previous.data != body.model_dump():
                    raise HTTPException(409, 'Idempotency key already used for different input')
                return public(previous)
        return public(create_record(db, ctx, kind, body.model_dump(), resource_key=key))
    def detail(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
        return public(get_record(db, ctx, kind, identifier))
    def update(identifier: str, body: dict, if_match: int | None=Header(None), ctx=Depends(require_write), db: Session = Depends(get_db)):
        record = get_record(db, ctx, kind, identifier, for_update=True)
        if if_match is not None and if_match != record.version:
            raise HTTPException(409, 'Resource version changed; reload before editing')
        try:
            data = schema.model_validate({**record.data, **body}).model_dump()
        except ValidationError as exc:
            raise HTTPException(422, str(exc))
        references(db, ctx, data)
        record.data = data
        audit(db, ctx, kind + ".updated", identifier)
        db.commit()
        return public(record)
    router.add_api_route("/" + kind, list_items, methods=["GET"], name="list_" + kind, response_model=list[response_schema])
    router.add_api_route("/" + kind, create_item, methods=["POST"], status_code=201, name="create_" + kind, response_model=response_schema)
    router.add_api_route("/" + kind + "/{identifier}", detail, methods=["GET"], name="get_" + kind, response_model=response_schema)
    router.add_api_route("/" + kind + "/{identifier}", update, methods=["PATCH"], name="update_" + kind, response_model=response_schema)


resource_routes("systems", SystemCreate)
for _kind in ("risks", "findings", "actions"):
    resource_routes(_kind, RiskCreate)


@router.get("/dashboard")
def dashboard(ctx=Depends(context), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Record.kind, func.count()).where(Record.tenant_id == ctx["tenant_id"]).group_by(Record.kind)).all())
    return {**{k: counts.get(k, 0) for k in ("systems", "risks", "findings", "actions", "evidence", "assessments", "executions", "policies")}, "counts": counts, "recent_activity": audit_list(ctx, db, None, 6, 0)}


@router.get("/frameworks")
def frameworks(ctx=Depends(context)):
    return [{"id": key, **value, "controls": new_controls(key)} for key, value in FRAMEWORKS.items()]


@router.get("/assessments")
def assessments(response: Response, limit: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0,le=1000000), ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in page(db, ctx, "assessments", response, limit, offset)]


@router.post("/assessments", status_code=201)
def create_assessment(body: AssessmentCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    return public(create_record(db, ctx, "assessments", {**body.model_dump(), "controls": new_controls(body.framework), "status": "in_progress"}))


@router.get("/assessments/{identifier}")
def assessment(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
    return public(get_record(db, ctx, "assessments", identifier))


@router.patch("/assessments/{identifier}")
def assessment_update(identifier: str, body: dict, if_match:int|None=Header(None),ctx=Depends(require_write), db: Session = Depends(get_db)):
    if set(body) - {"name", "status"} or body.get("status", "in_progress") not in {"in_progress", "completed"} or ("name" in body and (not isinstance(body["name"], str) or not 1 <= len(body["name"].strip()) <= 200)):
        raise HTTPException(422, "Only valid name and status changes are accepted")
    record = get_record(db, ctx, "assessments", identifier, for_update=True)
    if if_match is not None and if_match != record.version:
        raise HTTPException(409,'Assessment changed; reload before saving')
    from .workspaces import save_revision
    save_revision(db,ctx,record,'assessment')
    record.data = {**record.data, **body}
    audit(db, ctx, "assessment.updated", identifier)
    db.commit()
    return public(record)


@router.put("/assessments/{identifier}/controls/{control_id}")
def control_update(identifier: str, control_id: str, body: ControlUpdate, if_match:int|None=Header(None),ctx=Depends(require_write), db: Session = Depends(get_db)):
    record = get_record(db, ctx, "assessments", identifier, for_update=True)
    if if_match is not None and if_match != record.version:
        raise HTTPException(409,'Assessment changed; reload before saving')
    for evidence_id in body.evidence_ids:
        get_record(db, ctx, "evidence", evidence_id)
    controls = record.data["controls"]
    if not any(c["id"] == control_id for c in controls):
        raise HTTPException(404, "Unknown control")
    from .workspaces import save_revision
    save_revision(db,ctx,record,'assessment')
    record.data = {**record.data, "controls": [{**c, **body.model_dump()} if c["id"] == control_id else c for c in controls]}
    audit(db, ctx, "control.updated", identifier, {"control_id": control_id, "status": body.status})
    db.commit()
    return public(record)


@router.get("/bom")
def boms(response: Response, limit: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0,le=1000000), ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in page(db, ctx, "bom", response, limit, offset)]


@router.get('/bom/{identifier}/export')
def export_bom(identifier: str, ctx=Depends(context), db: Session=Depends(get_db)):
    record = get_record(db, ctx, 'bom', identifier)
    audit(db, ctx, 'bom.exported', identifier)
    db.commit()
    return Response(json.dumps(record.data['document']), media_type='application/vnd.cyclonedx+json', headers={'Content-Disposition':f'attachment; filename="{identifier}.cdx.json"'})


@router.post("/bom", status_code=201)
def import_bom(body: BomCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    document = body.document
    if document.get("bomFormat") != "CycloneDX" or document.get("specVersion") not in {"1.4", "1.5", "1.6", "1.7"} or not isinstance(document.get("components", []), list):
        raise HTTPException(422, "Expected CycloneDX JSON with supported specVersion and components array")
    # Structural import only; a full schema validator is an explicitly separate integration.
    raw = json.dumps(document, sort_keys=True).encode()
    if len(raw) > 2_000_000:
        raise HTTPException(413, "BOM exceeds 2 MB")
    components = document.get("components", [])
    if any(not isinstance(c, dict) or not isinstance(c.get("name"), str) for c in components):
        raise HTTPException(422, "Each component must be an object with a name")
    for component in components:
        for field in ('name','purl','version','group','type'):
            if field in component and (not isinstance(component[field],str) or not 1 <= len(component[field]) <= 2000):
                raise HTTPException(422,'Component identity fields must be bounded nonempty strings')
    lock_tenant(db,ctx)
    previous=db.scalar(select(Record).where(Record.tenant_id==ctx['tenant_id'],Record.kind=='bom',Record.data['system_id'].as_string()==body.system_id).order_by(Record.created_at.desc(),Record.id.desc()).limit(1))
    def component_identity(component):
        if component.get('purl'): return component['purl']
        name=(component.get('group','')+'/' if component.get('group') else '')+component['name']
        return name+('@'+component['version'] if component.get('version') else '')
    old = {component_identity(c) for c in previous.data["document"].get("components", [])} if previous else set()
    current = {component_identity(c) for c in components}
    data = {**body.model_dump(), "sha256": hashlib.sha256(raw).hexdigest(), "component_count": len(components), "validation": "structural_only",'previous_bom_id':previous.id if previous else None, "comparison": {"added": sorted(current-old), "removed": sorted(old-current)}}
    return public(create_record(db, ctx, "bom", data))


@router.get("/audit")
def audit_list(ctx=Depends(context), db: Session = Depends(get_db),response:Response=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000)):
    if response is not None:
        response.headers['X-Total-Count']=str(db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id==ctx['tenant_id'])))
        response.headers['X-Page-Limit']=str(limit)
        response.headers['X-Page-Offset']=str(offset)
    rows = db.scalars(select(Audit).where(Audit.tenant_id == ctx["tenant_id"]).order_by(Audit.created_at.desc(),Audit.id.desc()).limit(limit).offset(offset)).all()
    return [{"id": r.id, "actor_id": r.actor_id, "action": r.action, "resource_id": r.resource_id, "details": r.details, "previous_hash": r.previous_hash, "event_hash": r.event_hash, "created_at": r.created_at.replace(tzinfo=timezone.utc).isoformat()} for r in rows]


@router.get("/audit/verify")
def audit_verify(ctx=Depends(context), db: Session = Depends(get_db)):
    rows = db.scalars(select(Audit).where(Audit.tenant_id == ctx["tenant_id"]).order_by(Audit.created_at, Audit.id)).all()
    previous = "0" * 64
    for row in rows:
        payload = {"id": row.id, "tenant_id": row.tenant_id, "actor_id": row.actor_id, "action": row.action, "resource_id": row.resource_id, "details": row.details, "previous_hash": row.previous_hash, "created_at": row.created_at.replace(tzinfo=timezone.utc).isoformat()}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if previous != row.previous_hash or digest != row.event_hash:
            return {"valid": False, "events_checked": len(rows), "failed_event_id": row.id}
        previous = row.event_hash
    return {"valid": True, "events_checked": len(rows), "head_hash": previous, "scope": "Hash chain; not protection against privileged database rewriting"}


@router.get("/reports")
def reports(ctx=Depends(context), db: Session = Depends(get_db)):
    return [{"id": "workspace", "name": "Workspace governance report", "format": "json", "description": "Current tenant records, assessments and evidence hashes; generated on export."}]


@router.get("/reports/export")
def export_report(format: str = "json", ctx=Depends(context), db: Session = Depends(get_db)):
    if format != "json":
        raise HTTPException(422, "Supported export format: json")
    data = {"schema_version": "1.0", "tenant_id": ctx["tenant_id"], "notice": "Assessment support; not certification or a legal opinion.", "resources": {kind: [{k: v for k, v in public(r).items() if k not in {"content", "input", "raw_output", "config", "sanitized_text"}} for r in listed(db, ctx, kind)] for kind in ("systems", "risks", "findings", "actions", "assessments", "evidence", "bom", "governance_records", "runtime_reviews")}}
    audit(db, ctx, "report.exported", "workspace")
    db.commit()
    return Response(json.dumps(data, indent=2), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="governance-report.json"'})


@router.get("/settings")
def get_settings(ctx=Depends(context), db: Session = Depends(get_db)):
    rows = listed(db, ctx, "settings")
    return public(rows[0]) if rows else SettingsUpdate().model_dump()


@router.patch("/settings")
def update_settings(body: SettingsUpdate, ctx=Depends(require_admin), db: Session = Depends(get_db)):
    lock_tenant(db,ctx)
    rows = listed(db, ctx, "settings")
    if not rows:
        return public(create_record(db, ctx, "settings", body.model_dump(),resource_key='workspace'))
    record = rows[0]
    record.data = body.model_dump()
    audit(db, ctx, "settings.updated", record.id)
    db.commit()
    return public(record)
