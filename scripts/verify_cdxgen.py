"""Run the real integration against an explicit synthetic test fixture."""
import json
import os
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from integrations.discovery import ADAPTERS

manifest={'name':'uag-test-fixture','version':'1.0.0','dependencies':{'openai':'6.8.1'}}
input_data={'package_json':manifest,'package_lock':{'name':manifest['name'],'version':'1.0.0','lockfileVersion':3,
            'packages':{'':dict(manifest),'node_modules/openai':{'version':'6.8.1','license':'Apache-2.0'}}}}
result=ADAPTERS['cdxgen'].execute(input_data,{})
destination=ROOT/'docs'/'verification'/'cdxgen-test.json'
destination.parent.mkdir(parents=True,exist_ok=True)
record={'verified_at':'2026-11-13','fixture_kind':'Synthetic adapter test input, not client inventory or production monitoring',
        'command':'UAG_NODE_EXECUTABLE=<supported Node> .venv/Scripts/python.exe scripts/verify_cdxgen.py',
        'environment':{'os':os.name,'python':sys.version,'node':'24.22.3','cdxgen':'13.7.0'},
        'input':input_data,'observed':result.model_dump()}
destination.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result.status,'components':result.normalized.get('component_count'),'provenance':result.provenance,'error':result.error},indent=2))
if result.status!='succeeded':sys.exit(1)
