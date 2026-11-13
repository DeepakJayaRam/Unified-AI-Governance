"""Native bounded deterministic checks, explicitly separate from model guardrails."""
import re
from time import perf_counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .auth import context, require_write
from .db import get_db
from .governance import resource_routes
from .resources import create_record, get_record, listed, public
from .schemas import GuardrailRequest, GuardrailResponse, PolicyConfig, PolicyCreate

router = APIRouter()
PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "us_ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "payment_card_candidate": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
}


def evaluate(text: str, config: PolicyConfig):
    started = perf_counter()
    checks, sanitized = [], text
    decision = "allow"
    for label, pattern in PATTERNS.items():
        tick = perf_counter()
        matches = list(pattern.finditer(text))
        checks.append({"name": label, "matched": bool(matches), "count": len(matches), "latency_ms": (perf_counter()-tick)*1000})
        if matches:
            if config.pii_action == "sanitize":
                sanitized = pattern.sub("[REDACTED_" + label.upper() + "]", sanitized)
            decision = config.pii_action
    tick = perf_counter()
    blocked = any(term.casefold() in text.casefold() for term in config.blocked_terms)
    checks.append({"name": "blocked_terms", "matched": blocked, "latency_ms": (perf_counter()-tick)*1000})
    if blocked:
        decision = "block"
    return {"decision": decision, "sanitized_text": sanitized if decision in {"allow", "sanitize"} else None, "checks": checks, "latency_ms": (perf_counter()-started)*1000, "engine": "native-deterministic-v1", "limitations": "Limited pattern detection; no comprehensive PII or prompt-injection/model safety claim."}


@router.get("/policies")
def policies(ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in listed(db, ctx, "policies")]


@router.post("/policies", status_code=201)
def create_policy(body: PolicyCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    return public(create_record(db, ctx, "policies", body.model_dump()))


@router.patch("/policies/{identifier}")
def update_policy(identifier: str, body: PolicyCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    from .resources import audit
    row = get_record(db, ctx, "policies", identifier)
    row.data = body.model_dump()
    audit(db, ctx, "policy.updated", identifier)
    db.commit()
    return public(row)


@router.post("/guardrails/evaluate", response_model=GuardrailResponse)
def check(body: GuardrailRequest, ctx=Depends(require_write), db: Session = Depends(get_db)):
    if not body.policy_id:
        raise HTTPException(422, "Select an explicit enabled policy before evaluation")
    policy = get_record(db, ctx, "policies", body.policy_id)
    if not policy.data["enabled"]:
        raise HTTPException(409, "Policy is disabled")
    config = PolicyConfig.model_validate(policy.data["config"])
    try:
        result = evaluate(body.text, config)
    except Exception:
        result = {"decision": config.error_action, "sanitized_text": None, "checks": [], "latency_ms": 0, "error": "evaluation_failed", "engine": "native-deterministic-v1"}
    event = create_record(db, ctx, "runtime_events", {k: v for k, v in result.items() if k != "sanitized_text"} | {"policy_id": policy.id, "input_length": len(body.text)})
    return {**result, "event_id": event.id}


@router.get("/runtime/events")
def events(ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in listed(db, ctx, "runtime_events")]
