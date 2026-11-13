"""Private HTTP bridge to the genuine Presidio SDK; no prompt retention.

This application-owned bridge deliberately supports English and replacement
redaction only. It does not expose recognizer code, arbitrary models or actions.
"""
from typing import Literal
from importlib.metadata import version
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

nlp = NlpEngineProvider(nlp_configuration={
    'nlp_engine_name': 'spacy',
    'models': [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}],
}).create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=['en'])
anonymizer = AnonymizerEngine()
app = FastAPI(title='Private Presidio bridge', docs_url=None, redoc_url=None)


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse(status_code=422, content={'detail':'Invalid request; content omitted'})


@app.exception_handler(Exception)
async def internal_error(request, exc):
    return JSONResponse(status_code=503, content={'detail':'PII service unavailable'})


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Analyze(Strict):
    text: str = Field(min_length=1,max_length=32000)
    language: Literal['en'] = 'en'
    score_threshold: float = Field(default=0.5,ge=0,le=1)


class Span(Strict):
    start: int = Field(ge=0,strict=True)
    end: int = Field(ge=1,strict=True)
    score: float = Field(ge=0,le=1,allow_inf_nan=False)
    entity_type: str = Field(min_length=1,max_length=200)


class Replacement(Strict):
    type: Literal['replace']
    new_value: Literal['[REDACTED]']


class Anonymize(Strict):
    text: str = Field(min_length=1,max_length=32000)
    analyzer_results: list[Span] = Field(max_length=10000)
    anonymizers: dict[Literal['DEFAULT'], Replacement]


@app.get('/health')
def health():
    return {'status':'ok','analyzer':version('presidio-analyzer'),
            'anonymizer':version('presidio-anonymizer'),'model':'en_core_web_sm-3.8.0',
            'language':'en','entities':sorted(analyzer.get_supported_entities('en'))}


@app.post('/analyze')
def analyze(body:Analyze):
    return [result.to_dict() for result in analyzer.analyze(
        text=body.text,language=body.language,score_threshold=body.score_threshold,
        return_decision_process=False)]


@app.post('/anonymize')
def anonymize(body:Anonymize):
    if any(not 0 <= span.start < span.end <= len(body.text) for span in body.analyzer_results):
        raise HTTPException(422,'Invalid span offsets')
    result=anonymizer.anonymize(text=body.text,
        analyzer_results=[RecognizerResult(**span.model_dump()) for span in body.analyzer_results],
        operators={'DEFAULT':OperatorConfig('replace',{'new_value':'[REDACTED]'})})
    return {'text':result.text}


class BodyLimit:
    def __init__(self,app): self.app=app
    async def __call__(self,scope,receive,send):
        if scope['type'] != 'http':
            return await self.app(scope,receive,send)
        count=0
        messages=[]
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            count+=len(message.get('body',b''))
            if count>1_000_000:
                return await JSONResponse(status_code=413,content={'detail':'Request too large'})(scope,receive,send)
            messages.append(message)
            if not message.get('more_body'): break
        async def replay():
            return messages.pop(0) if messages else await receive()
        await self.app(scope,replay,send)


app.add_middleware(BodyLimit)
