"""Shared persistence operations. Every resource lookup requires tenant context."""
import hashlib
import json
from datetime import timezone
from fastapi import HTTPException
from sqlalchemy import select, text
from .db import Audit, Record, now, uid


def listed(db, ctx, kind):
    return db.scalars(select(Record).where(Record.tenant_id == ctx["tenant_id"], Record.kind == kind).order_by(Record.created_at.desc()).limit(1000)).all()


def get_record(db, ctx, kind, identifier):
    item = db.scalar(select(Record).where(Record.tenant_id == ctx["tenant_id"], Record.kind == kind, Record.id == identifier))
    if not item:
        raise HTTPException(404, "Resource not found")
    return item


def public(record):
    return {**record.data, "id": record.id, "created_at": record.created_at.replace(tzinfo=timezone.utc).isoformat(), "updated_at": record.updated_at.replace(tzinfo=timezone.utc).isoformat()}


def references(db, ctx, data):
    for field, kind in (("system_id", "systems"), ("finding_id", "findings")):
        if data.get(field):
            get_record(db, ctx, kind, data[field])


def audit(db, ctx, action, resource_id, details=None):
    # Serialize each tenant's audit chain in PostgreSQL, including first event.
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 0))"), {"tenant": ctx["tenant_id"]})
    previous = db.scalar(select(Audit).where(Audit.tenant_id == ctx["tenant_id"]).order_by(Audit.created_at.desc(), Audit.id.desc()).limit(1))
    event_id, stamp = uid(), now()
    payload = {"id": event_id, "tenant_id": ctx["tenant_id"], "actor_id": ctx["user_id"], "action": action, "resource_id": resource_id, "details": details or {}, "previous_hash": previous.event_hash if previous else "0" * 64, "created_at": stamp.isoformat()}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    row = Audit(**{**payload, "created_at": stamp}, event_hash=digest)
    db.add(row)
    db.flush()
    return row


def create_record(db, ctx, kind, data):
    references(db, ctx, data)
    record = Record(tenant_id=ctx["tenant_id"], kind=kind, data=data)
    db.add(record)
    db.flush()
    audit(db, ctx, kind + ".created", record.id)
    db.commit()
    return record
