"""Shared persistence operations. Every resource lookup requires tenant context."""
import hashlib
import json
from datetime import timezone
from fastapi import HTTPException
from sqlalchemy import select, text, func
from .db import Audit, Record, now, uid


def listed(db, ctx, kind, *, limit=None, offset=0):
    query = select(Record).where(Record.tenant_id == ctx["tenant_id"], Record.kind == kind).order_by(Record.created_at.desc(), Record.id.desc())
    if limit is not None:
        query = query.limit(limit).offset(offset)
    return db.scalars(query).all()


def page(db, ctx, kind, response, limit=100, offset=0):
    response.headers['X-Total-Count'] = str(db.scalar(select(func.count()).select_from(Record).where(Record.tenant_id == ctx['tenant_id'], Record.kind == kind)))
    response.headers['X-Page-Limit'] = str(limit)
    response.headers['X-Page-Offset'] = str(offset)
    return listed(db, ctx, kind, limit=limit, offset=offset)


def lock_tenant(db, ctx):
    # Serialize quota, singleton and membership decisions across API/worker processes.
    if db.bind.dialect.name == 'postgresql':
        db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 1))"), {'tenant':ctx['tenant_id']})


def get_record(db, ctx, kind, identifier, *, for_update=False):
    query = select(Record).where(Record.tenant_id == ctx["tenant_id"], Record.kind == kind, Record.id == identifier)
    if for_update:
        query = query.with_for_update()
    item = db.scalar(query)
    if not item:
        raise HTTPException(404, "Resource not found")
    return item


def public(record):
    return {**record.data, "id": record.id, "version": record.version, "created_at": record.created_at.replace(tzinfo=timezone.utc).isoformat(), "updated_at": record.updated_at.replace(tzinfo=timezone.utc).isoformat()}


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


def create_record(db, ctx, kind, data, *, resource_key=None, commit=True):
    references(db, ctx, data)
    record = Record(tenant_id=ctx["tenant_id"], kind=kind, data=data, resource_key=resource_key)
    db.add(record)
    db.flush()
    audit(db, ctx, kind + ".created", record.id)
    if commit:
        db.commit()
    return record
