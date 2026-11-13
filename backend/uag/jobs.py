"""Durable tenant-scoped jobs. Redis is notification only, never a pickle broker."""
import json
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from integrations.registry import adapters, catalog
from .auth import context, require_admin, require_write
from .config import settings
from .db import Record, SessionLocal, Tenant, get_db, now, set_tenant
from .resources import audit, create_record, get_record, listed, public
from .schemas import ExecutionCreate, IntegrationConfig

router = APIRouter()


def configured(db, ctx, identifier):
    return next((r for r in listed(db, ctx, "integration_configs") if r.data["integration_id"] == identifier), None)


def entry(identifier):
    match = next((r for r in catalog() if r["id"] == identifier), None)
    if not match:
        raise HTTPException(404, "Unknown integration")
    return match


@router.get("/integrations")
def integrations(ctx=Depends(context), db: Session = Depends(get_db)):
    actual = adapters()
    result = []
    for item in catalog():
        configuration = configured(db, ctx, item["id"])
        classification = item["classification"]
        status = "Planned"
        if classification == "REFERENCE_RESOURCE":
            status = "Reference only"
        elif classification == "BLOCKED_BY_LICENCE":
            status = "Licence restricted"
        elif item["id"] in actual:
            status = "Not configured"
            if configuration:
                status = configuration.data.get("health", {}).get("status", "Available") if configuration.data["enabled"] else "Disabled"
        result.append({**item, "status": status, "executable": item["id"] in actual, "configuration": configuration.data if configuration else None})
    return result


@router.put("/integrations/{identifier}/config")
def configure(identifier: str, body: IntegrationConfig, ctx=Depends(require_admin), db: Session = Depends(get_db)):
    item = entry(identifier)
    adapter = adapters().get(identifier)
    if not adapter or item["classification"] in {"REFERENCE_RESOURCE", "BLOCKED_BY_LICENCE", "DEFERRED"}:
        raise HTTPException(409, "This entry has no permitted executable adapter")
    if len(json.dumps(body.config)) > 16000:
        raise HTTPException(422, "Configuration too large")
    try:
        clean = adapter.validate_config(body.config)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc))
    data = {"integration_id": identifier, "enabled": body.enabled, "config": clean}
    record = configured(db, ctx, identifier)
    if record:
        record.data = data
        audit(db, ctx, "integration.configured", identifier)
        db.commit()
    else:
        record = create_record(db, ctx, "integration_configs", data)
    return public(record)


@router.post("/integrations/{identifier}/health")
def health(identifier: str, ctx=Depends(require_admin), db: Session = Depends(get_db)):
    adapter = adapters().get(identifier)
    row = configured(db, ctx, identifier)
    if not adapter or not row or not row.data["enabled"]:
        raise HTTPException(409, "Configure and enable the integration first")
    try:
        result = adapter.health(row.data["config"])
    except Exception:
        result = {"status": "Failed", "detail": "Health check failed; check service configuration"}
    result["status"] = {"connected": "Connected", "failed": "Failed", "not_configured": "Not configured", "available": "Available"}.get(result.get("status"), result.get("status", "Failed"))
    row.data = {**row.data, "health": result, "checked_at": now().isoformat()}
    audit(db, ctx, "integration.health", identifier, {"status": result["status"]})
    db.commit()
    return result


@router.get("/executions")
def executions(ctx=Depends(context), db: Session = Depends(get_db)):
    return [{k: v for k, v in public(r).items() if k not in {"input", "raw_output"}} for r in listed(db, ctx, "executions")]


@router.get("/executions/{identifier}")
def execution(identifier: str, ctx=Depends(context), db: Session = Depends(get_db)):
    result = public(get_record(db, ctx, "executions", identifier))
    if result.get("integration_id") == "presidio":
        result.pop("input", None)
    return result


@router.post("/executions", status_code=202)
def submit(body: ExecutionCreate, background: BackgroundTasks, ctx=Depends(require_write), db: Session = Depends(get_db)):
    item = entry(body.integration_id)
    if item["classification"] in {"REFERENCE_RESOURCE", "BLOCKED_BY_LICENCE", "DEFERRED"} or body.integration_id not in adapters():
        raise HTTPException(409, "Integration is not executable")
    configuration = configured(db, ctx, body.integration_id)
    if not configuration or not configuration.data["enabled"]:
        raise HTTPException(409, "Integration is not enabled")
    active = [r for r in listed(db, ctx, "executions") if r.data["status"] in {"queued", "running"}]
    if len(active) >= 10:
        raise HTTPException(429, "At most 10 outstanding executions per tenant")
    record = create_record(db, ctx, "executions", {**body.model_dump(), "status": "queued", "config_snapshot": configuration.data["config"], "actor_id": ctx["user_id"], "logs": []})
    if settings.execution_mode == "redis":
        from redis import Redis
        try:
            Redis.from_url(settings.redis_url, socket_timeout=2).rpush("uag:jobs", json.dumps({"tenant_id": ctx["tenant_id"], "job_id": record.id}))
        except Exception:
            # DB remains authoritative. Worker reconciliation recovers queued work.
            record.data = {**record.data, "logs": ["Notification unavailable; awaiting worker reconciliation"]}
            db.commit()
    else:
        background.add_task(run_job, ctx["tenant_id"], record.id)
    return public(record)


@router.post("/executions/{identifier}/cancel")
def cancel(identifier: str, ctx=Depends(require_write), db: Session = Depends(get_db)):
    record = get_record(db, ctx, "executions", identifier)
    if record.data["status"] not in {"queued", "running"}:
        raise HTTPException(409, "Execution is already terminal")
    record.data = {**record.data, "status": "cancelled", "finished_at": now().isoformat()}
    if record.data.get("integration_id") == "presidio":
        record.data = {key: value for key, value in record.data.items() if key != "input"}
    audit(db, ctx, "execution.cancelled", identifier)
    db.commit()
    return public(record)


def is_cancelled(tenant_id, job_id):
    with SessionLocal() as db:
        set_tenant(db, tenant_id)
        record = get_record(db, {"tenant_id": tenant_id}, "executions", job_id)
        return record.data["status"] == "cancelled"


def run_job(tenant_id, job_id):
    with SessionLocal() as db:
        set_tenant(db, tenant_id)
        row = get_record(db, {"tenant_id": tenant_id}, "executions", job_id)
        if row.data["status"] != "queued":
            return
        original = dict(row.data)
        running = {**original, "status": "running", "started_at": now().isoformat()}
        claimed = db.execute(update(Record).where(Record.id == job_id, Record.tenant_id == tenant_id, Record.data["status"].as_string() == "queued").values(data=running))
        db.commit()
        if not claimed.rowcount:
            return
    ctx = {"tenant_id": tenant_id, "user_id": original["actor_id"]}
    try:
        adapter = adapters()[original["integration_id"]]
        result = adapter.execute(original["input"], original["config_snapshot"], cancelled=lambda: is_cancelled(tenant_id, job_id))
        data = result.model_dump() if hasattr(result, "model_dump") else result
    except Exception as exc:
        data = {"status": "failed", "error": {"code": "adapter_failure", "message": "Adapter failed; review configuration and permitted input", "type": type(exc).__name__}, "logs": []}
    with SessionLocal() as db:
        set_tenant(db, tenant_id)
        row = get_record(db, ctx, "executions", job_id)
        if row.data["status"] == "cancelled":
            return
        row.data = {**running, **data, "finished_at": now().isoformat()}
        if original["integration_id"] == "presidio":
            row.data = {key: value for key, value in row.data.items() if key != "input"}
            normalized = dict(row.data.get("normalized", {}))
            normalized.pop("sanitized_text", None)
            row.data = {**row.data, "normalized": normalized, "privacy": "Original and sanitized prompt omitted from retained execution"}
        # Normalized findings retain original meaning; do not synthesize legal failures.
        for finding in data.get("normalized", {}).get("findings", [])[:1000]:
            db.add(Record(tenant_id=tenant_id, kind="findings", data={"title": str(finding.get("title", "Tool finding"))[:200], "description": str(finding.get("description", ""))[:10000], "severity": finding.get("severity", "info"), "status": "open", "system_id": original.get("system_id"), "execution_id": job_id, "owner": "", "due_date": None}))
        document = data.get("normalized", {}).get("bom")
        if original["integration_id"] == "cdxgen" and data.get("status") == "succeeded":
            document = data.get("raw_output", {}).get("bom")
        if document and original.get("system_id"):
            db.add(Record(tenant_id=tenant_id, kind="bom", data={"system_id": original["system_id"], "document": document, "execution_id": job_id, "component_count": len(document.get("components", [])), "validation": "upstream_generated"}))
        audit(db, ctx, "execution." + data["status"], job_id, {"integration_id": original["integration_id"]})
        db.commit()


def reconcile():
    # Worker enumerates tenant identifiers only, then enters each RLS context.
    pending = []
    with SessionLocal() as db:
        tenant_ids = list(db.scalars(select(Tenant.id)))
    for tenant_id in tenant_ids:
        with SessionLocal() as db:
            set_tenant(db, tenant_id)
            for row in listed(db, {"tenant_id": tenant_id}, "executions"):
                if row.data["status"] == "queued":
                    pending.append((tenant_id, row.id))
                elif row.data["status"] == "running" and row.updated_at.replace(tzinfo=now().tzinfo) < now() - timedelta(minutes=10):
                    # No automatic replay of non-idempotent integrations after worker loss.
                    row.data = {**row.data, "status": "failed", "error": {"code": "worker_interrupted", "message": "Worker lease expired; manual retry required"}}
                    if row.data.get("integration_id") == "presidio":
                        row.data = {key: value for key, value in row.data.items() if key != "input"}
            db.commit()
    for tenant_id, job_id in pending:
        run_job(tenant_id, job_id)


def worker():
    from redis import Redis
    client = Redis.from_url(settings.redis_url, socket_timeout=5)
    last_reconcile = 0
    while True:
        try:
            if time.monotonic()-last_reconcile > 30:
                reconcile()
                last_reconcile = time.monotonic()
            notification = client.blpop("uag:jobs", timeout=3)
            if notification:
                payload = json.loads(notification[1])
                run_job(payload["tenant_id"], payload["job_id"])
        except KeyboardInterrupt:
            return
        except Exception as exc:
            print("Worker retry:", type(exc).__name__, flush=True)
            time.sleep(2)
