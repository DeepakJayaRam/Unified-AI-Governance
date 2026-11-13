import hashlib
import json
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import ConfigDict, ValidationError, create_model
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .auth import context, require_admin, require_write
from .db import Audit, Record, get_db
from .frameworks import FRAMEWORKS, new_controls
from .resources import audit, create_record, get_record, listed, public, references
from .schemas import AssessmentCreate, BomCreate, ControlUpdate, RiskCreate, SettingsUpdate, SystemCreate

router = APIRouter()


def resource_routes(kind, schema):
    response_schema = create_model(kind.title() + "Record", __base__=schema, __config__=ConfigDict(extra="allow"), id=(str, ...), created_at=(str, ...), updated_at=(str, ...))
    def list_items(ctx=Depends(context), db: Session = Depends(get_db)):
        return [public(r) for r in listed(db, ctx, kind)]
    def create_item(body: schema, ctx=Depends(require_write), db: Session = Depends(get_db)):
        return public(create_record(db, ctx, kind, body.model_dump()))
    def detail(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
        return public(get_record(db, ctx, kind, identifier))
    def update(identifier: str, body: dict, ctx=Depends(require_write), db: Session = Depends(get_db)):
        record = get_record(db, ctx, kind, identifier)
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
    return {**{k: counts.get(k, 0) for k in ("systems", "risks", "findings", "actions", "evidence", "assessments", "executions", "policies")}, "counts": counts, "recent_activity": audit_list(ctx, db)[:6]}


@router.get("/frameworks")
def frameworks(ctx=Depends(context)):
    return [{"id": key, **value, "controls": new_controls(key)} for key, value in FRAMEWORKS.items()]


@router.get("/assessments")
def assessments(ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in listed(db, ctx, "assessments")]


@router.post("/assessments", status_code=201)
def create_assessment(body: AssessmentCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    return public(create_record(db, ctx, "assessments", {**body.model_dump(), "controls": new_controls(body.framework), "status": "in_progress"}))


@router.get("/assessments/{identifier}")
def assessment(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
    return public(get_record(db, ctx, "assessments", identifier))


@router.patch("/assessments/{identifier}")
def assessment_update(identifier: str, body: dict, ctx=Depends(require_write), db: Session = Depends(get_db)):
    if set(body) - {"name", "status"} or body.get("status", "in_progress") not in {"in_progress", "completed"} or ("name" in body and (not isinstance(body["name"], str) or not 1 <= len(body["name"].strip()) <= 200)):
        raise HTTPException(422, "Only valid name and status changes are accepted")
    record = get_record(db, ctx, "assessments", identifier)
    record.data = {**record.data, **body}
    audit(db, ctx, "assessment.updated", identifier)
    db.commit()
    return public(record)


@router.put("/assessments/{identifier}/controls/{control_id}")
def control_update(identifier: str, control_id: str, body: ControlUpdate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    record = get_record(db, ctx, "assessments", identifier)
    for evidence_id in body.evidence_ids:
        get_record(db, ctx, "evidence", evidence_id)
    controls = record.data["controls"]
    if not any(c["id"] == control_id for c in controls):
        raise HTTPException(404, "Unknown control")
    record.data = {**record.data, "controls": [{**c, **body.model_dump()} if c["id"] == control_id else c for c in controls]}
    audit(db, ctx, "control.updated", identifier, {"control_id": control_id, "status": body.status})
    db.commit()
    return public(record)


@router.get("/bom")
def boms(ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in listed(db, ctx, "bom")]


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
    previous = [r for r in listed(db, ctx, "bom") if r.data["system_id"] == body.system_id]
    old = {c.get("purl", c["name"]) for c in previous[0].data["document"].get("components", [])} if previous else set()
    current = {c.get("purl", c["name"]) for c in components}
    data = {**body.model_dump(), "sha256": hashlib.sha256(raw).hexdigest(), "component_count": len(components), "validation": "structural_only", "comparison": {"added": sorted(current-old), "removed": sorted(old-current)}}
    return public(create_record(db, ctx, "bom", data))


@router.get("/audit")
def audit_list(ctx=Depends(context), db: Session = Depends(get_db)):
    rows = db.scalars(select(Audit).where(Audit.tenant_id == ctx["tenant_id"]).order_by(Audit.created_at.desc()).limit(1000)).all()
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
    data = {"schema_version": "1.0", "tenant_id": ctx["tenant_id"], "notice": "Assessment support; not certification or a legal opinion.", "resources": {kind: [{k: v for k, v in public(r).items() if k not in {"content", "input", "raw_output", "config", "sanitized_text"}} for r in listed(db, ctx, kind)] for kind in ("systems", "risks", "findings", "actions", "assessments", "evidence", "bom")}}
    audit(db, ctx, "report.exported", "workspace")
    db.commit()
    return Response(json.dumps(data, indent=2), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="governance-report.json"'})


@router.get("/settings")
def get_settings(ctx=Depends(context), db: Session = Depends(get_db)):
    rows = listed(db, ctx, "settings")
    return public(rows[0]) if rows else SettingsUpdate().model_dump()


@router.patch("/settings")
def update_settings(body: SettingsUpdate, ctx=Depends(require_admin), db: Session = Depends(get_db)):
    rows = listed(db, ctx, "settings")
    if not rows:
        return public(create_record(db, ctx, "settings", body.model_dump()))
    record = rows[0]
    record.data = body.model_dump()
    audit(db, ctx, "settings.updated", record.id)
    db.commit()
    return public(record)
