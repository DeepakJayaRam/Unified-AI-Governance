"""Typed governance records, assessment history, and source-traceable crosswalks."""
import json
from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header
from pydantic import Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .auth import context, require_write
from .db import Record, get_db
from .frameworks import FRAMEWORKS
from .resources import audit, create_record, get_record, listed, page, public
from .schemas import Strict

router = APIRouter()


class GovernanceRecord(Strict):
    framework: Literal['eu_ai_act','iso42001','nist_ai_rmf']
    kind: Literal['classification','applicability','obligation','scope','objective','management_review','internal_audit','risk_treatment','reassessment']
    title: str = Field(min_length=1,max_length=200)
    system_id: str
    assessment_id: str | None = None
    risk_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list,max_length=100)
    owner: str = Field(default='',max_length=254)
    status: Literal['draft','in_progress','approved','closed'] = 'draft'
    rationale: str = Field(default='',max_length=20000)
    decision: str = Field(default='',max_length=2000)
    due_date: str | None = None
    source_url: str = Field(default='',max_length=2000,pattern=r'^(https://[^\s]+)?$')
    source_version: str = Field(default='',max_length=200)

    @field_validator('due_date')
    @classmethod
    def valid_date(cls, value):
        return date.fromisoformat(value).isoformat() if value else None


def validate_links(db,ctx,data):
    system = get_record(db,ctx,'systems',data['system_id'])
    for key,kind in [('assessment_id','assessments'),('risk_id','risks')]:
        if data.get(key):
            target=get_record(db,ctx,kind,data[key])
            if target.data.get('system_id') != system.id:
                raise HTTPException(422,'Linked record belongs to a different AI system')
            if kind == 'assessments' and target.data['framework'] != data['framework']:
                raise HTTPException(422, 'Assessment belongs to a different framework')
    for identifier in data['evidence_ids']:
        get_record(db,ctx,'evidence',identifier)
    if data['status'] in {'approved', 'closed'} and ctx['role'] == 'contributor':
        raise HTTPException(403, 'A manager or administrator must approve or close governance records')


@router.get('/governance-records')
def records(response: Response, framework: str | None=None, limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=1000000),ctx=Depends(context),db:Session=Depends(get_db)):
    query=select(Record).where(Record.tenant_id==ctx['tenant_id'],Record.kind=='governance_records')
    if framework:
        query=query.where(Record.data['framework'].as_string()==framework)
    response.headers['X-Total-Count'] = str(db.scalar(select(func.count()).select_from(query.subquery())))
    response.headers['X-Page-Limit'] = str(limit)
    response.headers['X-Page-Offset'] = str(offset)
    return [public(r) for r in db.scalars(query.order_by(Record.created_at.desc(), Record.id.desc()).limit(limit).offset(offset))]


@router.post('/governance-records',status_code=201)
def create(body:GovernanceRecord,ctx=Depends(require_write),db:Session=Depends(get_db)):
    data=body.model_dump()
    validate_links(db,ctx,data)
    return public(create_record(db,ctx,'governance_records',data))


@router.patch('/governance-records/{identifier}')
def update(identifier:str,body:GovernanceRecord,if_match:int|None=Header(None),ctx=Depends(require_write),db:Session=Depends(get_db)):
    record=get_record(db,ctx,'governance_records',identifier,for_update=True)
    if if_match is not None and if_match != record.version:
        raise HTTPException(409, 'Record changed; reload before saving')
    data=body.model_dump()
    validate_links(db,ctx,data)
    save_revision(db,ctx,record,'governance_record')
    record.data=data
    audit(db,ctx,'governance_record.updated',identifier,{'kind':body.kind,'status':body.status})
    db.commit()
    return public(record)


def save_revision(db,ctx,record,kind):
    db.add(Record(tenant_id=ctx['tenant_id'],kind=kind+'_versions',resource_key=f'{record.id}:{record.version}',data={'resource_id':record.id,'revision':record.version,'snapshot':record.data,'actor_id':ctx['user_id']}))
    # Explicitly advance even when an operator saves the same content again.
    record.version += 1


@router.get('/assessments/{identifier}/history')
def assessment_history(identifier:str,ctx=Depends(context),db:Session=Depends(get_db)):
    get_record(db,ctx,'assessments',identifier)
    return [public(r) for r in db.scalars(select(Record).where(Record.tenant_id==ctx['tenant_id'],Record.kind=='assessment_versions',Record.data['resource_id'].as_string()==identifier).order_by(Record.created_at.desc()))]


@router.get('/assessments/{identifier}/export')
def assessment_export(identifier:str,ctx=Depends(context),db:Session=Depends(get_db)):
    record=get_record(db,ctx,'assessments',identifier)
    data={'schema_version':'1.0','assessment':public(record),'framework_source':FRAMEWORKS[record.data['framework']]['source_url'],'history':assessment_history(identifier,ctx,db),'notice':'Original assessment support; not certification or a legal determination.'}
    audit(db,ctx,'assessment.exported',identifier)
    db.commit()
    return Response(json.dumps(data),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="assessment-{identifier}.json"'})


@router.get('/frameworks/crosswalks')
def crosswalks(ctx=Depends(context)):
    topics=[('Accountability','EU-SCOPE','AIMS-POLICY','GOVERN'),('Risk and impact assessment','EU-RISK','AIMS-RISK','MAP'),('Evaluation evidence','EU-SECURITY','AIMS-IMPROVE','MEASURE'),('Monitoring and response','EU-HUMAN','AIMS-IMPROVE','MANAGE')]
    return [{'id':f'uag-crosswalk-{i}','topic':topic,'mapping_version':'uag-original-0.2','relation':'related governance topic; not normative equivalence','sources':[{'framework':framework,'control_id':control,'source_url':FRAMEWORKS[framework]['source_url'],'source_version':version} for framework,control,version in [('eu_ai_act',eu,'Regulation (EU) 2024/1689; assess current amendments'),('iso42001',iso,'ISO/IEC 42001:2023; original application prompts'),('nist_ai_rmf',nist,'NIST AI RMF 1.0 (2023)')]]} for i,(topic,eu,iso,nist) in enumerate(topics,1)]
