"""Native bounded deterministic checks, explicitly separate from model guardrails."""
import re
from time import perf_counter
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Response
from pydantic import Field
from typing import Literal
from sqlalchemy import select
from sqlalchemy.orm import Session
from .auth import context, require_write
from .db import get_db, Record
from .governance import resource_routes
from .resources import audit, create_record, get_record, listed, public, page
from .schemas import GuardrailRequest, GuardrailResponse, PolicyConfig, PolicyCreate, Strict
from .workspaces import save_revision

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
def policies(response:Response,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000),ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in page(db, ctx, "policies",response,limit,offset)]


@router.post("/policies", status_code=201)
def create_policy(body: PolicyCreate, ctx=Depends(require_write), db: Session = Depends(get_db)):
    return public(create_record(db, ctx, "policies", body.model_dump()))


@router.patch("/policies/{identifier}")
def update_policy(identifier: str, body: PolicyCreate, if_match:int|None=Header(None),ctx=Depends(require_write), db: Session = Depends(get_db)):
    from .resources import audit
    row = get_record(db, ctx, "policies", identifier,for_update=True)
    if if_match is not None and if_match!=row.version:
        raise HTTPException(409,'Policy changed; reload before saving')
    save_revision(db,ctx,row,'policy')
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
    system = get_record(db,ctx,'systems',body.system_id) if body.system_id else None
    started = perf_counter()
    result = {'decision':'allow','sanitized_text':body.text,'checks':[], 'engine':'configured-pipeline-v1',
              'limitations':'Only selected controls execute. Native patterns do not provide comprehensive PII or prompt-injection protection.'}
    active_control = 'native'
    try:
        if 'native' in config.checks:
            result.update(evaluate(body.text, config))
        for check in result['checks']:
            check['status']='executed'
        ranks={'allow':0,'sanitize':1,'review':2,'block':3}
        from integrations.runtime_security import ADAPTERS
        from .jobs import configured
        for identifier in ['presidio','opa']:
            if identifier not in config.checks:
                continue
            active_control = identifier
            configuration = configured(db,ctx,identifier)
            if not configuration or not configuration.data['enabled']:
                action = config.error_action
                result['checks'].append({'name':identifier,'status':'not_configured','decision':action,'latency_ms':0,'reason':'Tenant integration must be enabled by an administrator'})
                if ranks[action] > ranks[result['decision']]:
                    result['decision'] = action
                continue
            adapter=ADAPTERS[identifier]
            adapter_config={**configuration.data['config'],'error_action':config.error_action}
            if identifier == 'presidio':
                adapter_config['action'] = config.pii_action
            # Compose transformations so a later service cannot restore text redacted earlier.
            input_data={'text':result.get('sanitized_text') or body.text} if identifier=='presidio' else {'risk_level':system.data['risk_level'] if system else 'unassessed','contains_pii':any(c.get('matched') for c in result['checks'] if c['name'] in {*PATTERNS, 'presidio'})}
            outcome=adapter.execute(input_data,adapter_config)
            action=outcome.normalized.get('action',config.error_action)
            if action == 'sanitize' and (identifier == 'opa' or outcome.normalized.get('sanitized_text') is None):
                raise ValueError('Sanitize requires a verified text transformation')
            result['checks'].append({'name':identifier,'status':'executed' if outcome.status=='succeeded' else 'failed','decision':action,'latency_ms':outcome.normalized.get('latency_ms',0),'matched':bool(outcome.normalized.get('entities')),'reason':outcome.error.get('code') if outcome.error else 'configured control evaluated'})
            if ranks[action]>ranks[result['decision']]:
                result['decision']=action
            if action=='sanitize' and outcome.normalized.get('sanitized_text') is not None:
                result['sanitized_text']=outcome.normalized['sanitized_text']
    except Exception:
        result['decision'] = 'block' if result['decision'] == 'block' else config.error_action
        result['error'] = 'evaluation_failed'
        result['checks'].append({'name':active_control,'status':'failed','decision':result['decision'],'reason':'evaluation_failed'})
    result['engine']='configured-pipeline-v1'
    result['latency_ms']=(perf_counter()-started)*1000
    if result['decision'] in {'block','review'}:
        result['sanitized_text']=None
    event = create_record(db, ctx, "runtime_events", {k: v for k, v in result.items() if k != "sanitized_text"} | {"policy_id": policy.id,'policy_version':policy.version,'direction':body.direction,'system_id':body.system_id, "input_length": len(body.text)}, commit=False)
    if result['decision']=='review':
        create_record(db,ctx,'runtime_reviews',{'event_id':event.id,'policy_id':policy.id,'status':'pending','resolution':None,'notes':'','owner':''},commit=False)
    db.commit()
    return {**result, "event_id": event.id}


@router.get("/runtime/events")
def events(response:Response,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000),ctx=Depends(context), db: Session = Depends(get_db)):
    return [public(r) for r in page(db, ctx, "runtime_events",response,limit,offset)]


@router.get('/policies/{identifier}/versions')
def versions(identifier:str,ctx=Depends(context),db:Session=Depends(get_db)):
    get_record(db,ctx,'policies',identifier)
    return [public(r) for r in db.scalars(select(Record).where(Record.tenant_id==ctx['tenant_id'],Record.kind=='policy_versions',Record.data['resource_id'].as_string()==identifier).order_by(Record.created_at.desc()))]


class Rollback(Strict):
    revision:int=Field(ge=1)


@router.post('/policies/{identifier}/rollback')
def rollback(identifier:str,body:Rollback,if_match:int|None=Header(None),ctx=Depends(require_write),db:Session=Depends(get_db)):
    row=get_record(db,ctx,'policies',identifier,for_update=True)
    if if_match is not None and if_match!=row.version:
        raise HTTPException(409,'Policy changed; reload before rollback')
    historical=db.scalar(select(Record).where(Record.tenant_id==ctx['tenant_id'],Record.kind=='policy_versions',Record.resource_key==f'{identifier}:{body.revision}'))
    if not historical:
        raise HTTPException(404,'Policy revision not found')
    save_revision(db,ctx,row,'policy')
    row.data=historical.data['snapshot']
    audit(db,ctx,'policy.rolled_back',identifier,{'restored_revision':body.revision})
    db.commit()
    return public(row)


@router.get('/runtime/reviews')
def reviews(response:Response,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000),ctx=Depends(context),db:Session=Depends(get_db)):
    return [public(r) for r in page(db,ctx,'runtime_reviews',response,limit,offset)]


class ReviewResolution(Strict):
    resolution:Literal['allow','block']
    notes:str=Field(min_length=1,max_length=5000)
    owner:str=Field(default='',max_length=254)


@router.patch('/runtime/reviews/{identifier}')
def resolve_review(identifier:str,body:ReviewResolution,ctx=Depends(require_write),db:Session=Depends(get_db)):
    if ctx['role']=='contributor':
        raise HTTPException(403,'A governance manager or security engineer must resolve reviews')
    row=get_record(db,ctx,'runtime_reviews',identifier,for_update=True)
    if row.data['status']!='pending':
        raise HTTPException(409,'Review already resolved')
    row.data={**row.data,**body.model_dump(),'status':'resolved','reviewer_id':ctx['user_id']}
    audit(db,ctx,'runtime.review_resolved',identifier,{'resolution':body.resolution})
    db.commit()
    return public(row)
