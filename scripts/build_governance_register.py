"""Curate verified metadata from the read-only inspection scripts."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/'tmp/governance-research.json').read_text(encoding='utf8'))
extra=json.loads((ROOT/'tmp/governance-extras.json').read_text(encoding='utf8'))
m3=json.loads((ROOT/'tmp/m3-research.json').read_text(encoding='utf8'))
by_number={r['number']:r for r in raw+[m3]}
records=[]

def add(number,slug,name,layer,classification,version,capabilities,languages,installation,dependencies,api,sdk,cli,deployment,input_formats,output_formats,licence,maintenance,integration_method,security_risks,source_url=None):
    inspected=by_number.get(number,{})
    sources=[{'url':f['url'],'sha256':f['sha256']} for f in inspected.get('files',[]) if 'text' in f]
    records.append(dict(number=number,id=slug,name=name,layer=layer,source_url=source_url or 'https://github.com/'+inspected['repository'],classification=classification,version=version,inspected_commit=inspected.get('commit'),verified_at='2026-11-13',capabilities=capabilities,languages=languages,installation=installation,dependencies=dependencies,api=api,sdk=sdk,cli=cli,deployment=deployment,input_formats=input_formats,output_formats=output_formats,licence=licence,maintenance=maintenance,integration_method=integration_method,security_risks=security_risks,test_status='SOURCE_VERIFIED_NOT_EXECUTED',sources=sources))

add(1,'cdxgen','OWASP cdxgen',1,'CLI_INTEGRATION','npm stable 13.7.0; inspected HEAD manifest 13.8.0 (not selected)',
 ['Generate CycloneDX inventory from source manifests and supported ecosystems','AI/ML inventory depends on discovered metadata; an SBOM is not proof of all AI usage'],['JavaScript','TypeScript','Python helper metadata'],
 'npm install --save-exact @cdxgen/cdxgen@13.7.0 in an isolated tooling directory; Node >=24',
 ['Node >=24','Ecosystem-specific tools for richer analysis','Optional platform plugins'],
 'Optional server mode documented; no network service selected','JavaScript package exports verified in package.json','cdxgen and aibom binaries verified',
 'Official container documented; local restricted CLI selected',['package manifests','lock files','source trees','supported container inputs'],['CycloneDX JSON'],
 'Apache-2.0; preserve licence/notices and dependency licences',
 'Repository accessible. Stable npm and development HEAD differ; pin stable. Language coverage varies with installed toolchains.',
 'Restricted CLI over staged package manifests; no arbitrary paths or user arguments. Disable dependency installation and network features.',
 ['Dependency scripts and external tool invocation','Source/manifest secrets in output','Resource exhaustion','Do not equate inventory with vulnerability detection'])
add(2,'owasp-aibom','OWASP AIBOM Generator',1,'DEFERRED','HEAD pyproject 1.0.2; PyPI name owasp-aibom-generator returned 404',
 ['Extract Hugging Face model metadata','Generate CycloneDX 1.6 JSON','AIBOM completeness scoring'],['Python','HTML'],
 'Upstream documents pip install -r requirements.txt or uv sync from source; python -m src.cli owner/model',
 ['Python >=3.11','cyclonedx-python-lib','huggingface_hub','torch','transformers','datasets'],
 'README declares API endpoints; precise interface not yet exercised','Source Python modules, no independently verified SDK contract','src.cli and aibom entry point verified',
 'python -m src.main documented; no production deployment validated',['Hugging Face model ID','optional metadata overrides'],['CycloneDX 1.6 JSON','completeness metrics'],
 'Apache-2.0 stated in licence and manifest; model/dataset licences remain separate',
 'Repository accessible. Heavy dependencies and unpublished package name require isolated source build and runtime tests.',
 'Await isolated service deployment, model egress allowlist and contract test; catalogue link available.',
 ['Model repository untrusted metadata','Remote inference option requires credentials','Large downloads','PII or confidential model IDs sent externally'])
add(3,'opencomplai','OpenComplAI Scan',1,'DEFERRED','opencomplai-cli 0.15.0 (PyPI 2026-11-08)',
 ['Deterministic code/manifest discovery and findings','Compliance manifest checks','EU AI Act evaluated; NIST projection and attestation-led framework packs are distinct','Scanner advisory mode documented; check exit codes have different semantics'],['Python','TypeScript'],
 'Upstream: pip install opencomplai-cli==0.15.0; not bundled by this application',
 ['Python >=3.11','opencomplai-core','Typer','Rich','Pydantic'],
 'Separate gateway/services documented; not configured','opencomplai Python SDK package exists','opencomplai scan --quick and scan --manifest ... --repo-root ... documented',
 'Upstream Compose exists under infra/compose; separate deployment only pending licence assessment',
 ['Repository files','system-manifest.json','scan baseline JSON'],['scan-report.json','compliance-artifact.json','structured findings'],
 'AGPL-3.0-only Community Edition; network-use/source obligations must be assessed before embedding or hosted deployment; commercial Enterprise licence offered',
 'Accessible active source; stable CLI verified through PyPI. Documentation explicitly distinguishes discovery and compliance gates.',
 'Deferred pending AGPL distribution/network obligation decision and isolated CLI tests. No source copied or package included.',
 ['Scan can read sensitive files; use .ocignore plus app staging allowlist','Optional push and model inference must remain disabled','Advisory findings are not compliance certification'])
add(4,'riskforge','RiskForge by AI Exponent',2,'DEFERRED','riskforge 2.1.0 (PyPI 2026-11-07)',
 ['Guided Article 9 risk assessment','Risk Management File exports','Hash-chained audit trail and verification features','Human input drives assessment; no legal certification'],['Python'],
 'pip install riskforge==2.1.0 in separate environment; PDF requires platform libraries described upstream',
 ['Python >=3.11','Typer <0.26','Pydantic 2','WeasyPrint 70','cryptography','PyYAML','jsonschema'],
 'No supported HTTP service verified','Python modules and plugin entry points; no stable external SDK contract validated','riskforge CLI verified in manifest; init, assess and export workflows documented',
 'Local offline CLI; PDF system dependencies require separate packaging',['System metadata','guided answers','YAML answers','imported evidence JSON'],['Risk Management File JSON','Markdown','PDF'],
 'Apache-2.0; preserve notices and review dependent libraries',
 'Actual repo aiexponent/riskforge verified by PyPI project URLs. Website snippets can lag current package; dependency bounds matter.',
 'Await isolated CLI installation and noninteractive workflow contract tests; native application assessment stores evidence meanwhile.',
 ['Local audit files contain sensitive risk information','Plugin code execution','PDF resource loading','Hash chains alone do not prevent privileged tampering'])
add(5,'eu-ai-act-toolkit','EU AI Act Toolkit (AbdelStark)',2,'DEFERRED','Source SDK and CLI 0.1.0; both npm package latest URLs returned 404',
 ['Deterministic TypeScript classification and checklists','Markdown templates with placeholders','CLI JSON reports','Static browser workspace'],['TypeScript','JavaScript'],
 'README proposes npm @eu-ai-act/sdk and npx @eu-ai-act/cli, but registry 404 observed; source build requires npm install then turbo build',
 ['Node >=20','TypeScript','Turborepo','SDK manifest has no runtime dependencies'],
 'No backend API; web app is client-side','Source @eu-ai-act/sdk exists; registry installation not verified','Source @eu-ai-act/cli exists; registry installation not verified',
 'Static Next.js app and local CLI source; no container verified',['Classification questionnaire','risk tier','template metadata'],['Classification JSON','checklist JSON','Markdown templates'],
 'MIT; retain copyright and licence if source is redistributed',
 'Source accessible; advertised published package availability failed. README legal dates differ from 2026 EUR-Lex amendment; review content before reuse.',
 'Reference link and native assessment workflow now; defer package adapter until source-built artifact and legal mappings validated.',
 ['Classification may omit legal exceptions','Stale regulatory dates','Do not automatically treat score as compliance'])
add(6,'venturalitica','Venturalitica SDK',2,'DEFERRED','venturalitica 0.8.2 (PyPI 2026-08-27)',
 ['Training-time data/fairness policy checks','Trace and model-BOM evidence','OSCAL policy and result workflows claimed upstream','Regulatory documentation drafts'],['Python'],
 'pip install venturalitica==0.8.2; disable analytics with VENTURALITICA_NO_ANALYTICS=1 or DO_NOT_TRACK',
 ['Python >=3.11','numpy >=2.4','pandas','scikit-learn','compliance-trestle','cyclonedx-python-lib','posthog'],
 'No hosted API used; cloud described as forthcoming','vl.enforce, vl.monitor, vl.retain documented','vl / venturalitica entry points verified',
 'Local SDK; optional dashboard and model extras',['pandas DataFrame','OSCAL policy YAML','training artifacts'],['Audit trace JSON','CycloneDX ML-BOM','OSCAL assessment-results claimed; not validated here'],
 'Apache-2.0; model/cloud terms separate',
 'Beta classifier in package manifest. Version verified; heavy scientific dependencies should be isolated from core.',
 'Deferred to data-science worker after representative dataset and OSCAL format tests; never claim compatibility from README alone.',
 ['Telemetry enabled unless opted out','Optional cloud fallback for LLM generation','Potential sensitive dataset/evidence traces','Heavy CPU/GPU processing'])
add(7,'compl-ai','COMPL-AI',2,'DEFERRED','HEAD pyproject 2.0.0; no tagged stable release found by git ls-remote',
 ['LLM technical benchmark suite built on Inspect AI','Provider API and local model evaluations','Sample-level evaluation logs','v1 and v2 scores not directly comparable'],['Python'],
 'Upstream: source clone then uv sync, use complai eval provider/model; pin inspected commit when trialled',
 ['Python >=3.11,<3.14','Inspect AI','PyTorch','datasets','spaCy','multiple Git-sourced packages','provider credentials or local model hardware'],
 'Provider APIs consumed, not an application governance API','Inspect AI task plugins','complai eval/list/samples/predict documented',
 'Separate evaluation environment; agentic tasks may use sandboxes',['Model/provider ID','task YAML/JSON','datasets'],['Inspect evaluation logs','JSONL samples','predicted score JSON'],
 'Apache-2.0 main project; benchmark datasets, models and third-party tasks have separate licences',
 'Accessible; framework mapping update in progress per README. Python 3.14 host incompatible with current declared bound.',
 'Asynchronous isolated evaluation only; awaiting Python <=3.13 environment and model/provider configuration.',
 ['Cost and remote data transfer','GPU/CPU and sandbox requirements','Untrusted benchmark content','Benchmark score is not legal conformity'])
add(8,'awesome-eu-ai-act','Awesome EU AI Act',2,'REFERENCE_RESOURCE','Commit inspected; no versioned executable release',
 ['Curated links to EU AI Act resources, tools and frameworks'],['Markdown'],
 'No installation; visit or pin reference URL',[], 'None','None','None','Static repository reference',[],['Human-readable reference links'],
 'README dedicates work under CC0-1.0; linked projects retain their own terms',
 'Repository accessible. Curated third-party claims require independent verification.',
 'Reference catalogue only; not executable and never shown as connected.',
 ['Link rot','Non-authoritative legal summaries','Linked tools may have incompatible licences'])
add(9,'iso-42001-toolkit','ISO/IEC 42001 AI Governance Toolkit (Ankit Uniyal)',3,'REFERENCE_RESOURCE','Commit inspected; assessment checker 1.1.0, SoA tracker 1.0.0 in source; no project release tag',
 ['AIMS templates and registers','Gap-assessment guidance and cross-framework references','CSV assessment-age checker','JSON SoA progress tracker with CSV export'],['Markdown','Python'],
 'Reference documents need no install. Optional upstream scripts use Python standard library; scripts not bundled.',
 ['Python standard library for optional scripts','Licensed ISO standard for authoritative requirements'],
 'None verified','None verified','15-SCRIPTS/ai_assessment_checker.py and aims_soa_tracker.py inspected',
 'Documents and local optional scripts; no service',['CSV system assessment dates','SoA JSON state','human-entered governance records'],['Text assessment report','SoA JSON','CSV'],
 'MIT for toolkit repository. This does not grant rights to reproduce ISO/IEC standard text or claim certification.',
 'Source accessible. README indexes current files; feature counts are upstream claims, not independently audited ISO completeness.',
 'Reference catalogue; native AIMS register stores user decisions and original short prompts, without copying ISO clauses.',
 ['Sensitive registers','Template/standard rights distinction','Do not claim full standard coverage or certification'])
add(10,'eu-ai-act-compliance-toolkit','EU AI Act Compliance Toolkit (Ankit Uniyal)',3,'DEFERRED','README heading 3.5.0; footer 3.4.0; pyproject classifier 2.1.0; README script 2.2; commit is authoritative identifier',
 ['Governance templates and scorecards','Risk-tier classifier source','CSV inventory processing with JSON/text/CSV reports'],['Markdown','Python'],
 'Do not install or copy until a licence grant is located. Upstream documents python scripts/risk_classifier.py.',
 ['Python >=3.9','No package dependencies declared'],
 'None verified','None verified','eu-ai-risk-classify entry point in pyproject and source script documented',
 'Documents and local script; no service',['CSV AI inventory'],['Text','JSON','CSV','Markdown templates'],
 'UNVERIFIED: LICENSE, LICENSE.md and LICENSE.txt return 404; GitHub root file listing shows no licence. pyproject says See repository LICENSE. Public source alone is not a reuse grant.',
 'Source accessible but conflicting versions and missing licence prevent safe incorporation.',
 'External reference link only. Defer script/template redistribution and adapter installation until licence resolved.',
 ['Missing licence','Legal classification needs professional review','Conflicting versions','Never treat generated clearance certificate as legal approval'])
add(11,'ai-atlas-nexus','IBM AI Atlas Nexus (formerly Risk Atlas Nexus)',4,'DEFERRED','ai-atlas-nexus 1.2.5 (PyPI 2026-08-31)',
 ['Risk and governance knowledge graph','Cross-taxonomy querying','Risk identification using optional LLM inference','JSON/YAML graph queries'],['Python'],
 'pip install ai-atlas-nexus==1.2.5 in isolated compatible environment; extras for chosen inference provider',
 ['LinkML','SSSOM','txtai','datasets','mellea','pyoxigraph','pyshacl','optional Ollama/vLLM/Watsonx'],
 'Consumes model APIs; no standalone HTTP API selected','Python AI Atlas Nexus APIs','ran and ran-extension entry points verified; ran query emits JSON/YAML',
 'Local package plus optional separate inference service',['Knowledge graph records','AI system/task descriptions','query filters'],['JSON','YAML','risk/task identification records'],
 'Apache-2.0 main repository; imported taxonomy and model terms require per-artifact review',
 'README Python target is stale; HEAD manifest >=3.11,<=3.14.7 while PyPI 1.2.5 declares <3.14.4. Validate exact environment before install.',
 'Deferred package/query worker until dependency lock, taxonomy provenance and representative query test; NIST reference linked now.',
 ['Optional automatic model download','External provider credentials/data','Large model dependencies','Mappings do not establish equivalent compliance'])
add(12,'nist-airc','NIST AI Resource Center / AI RMF',4,'REFERENCE_RESOURCE','AI RMF 1.0 (2023) reference; website states revision in progress',
 ['Authoritative AI RMF Govern, Map, Measure, Manage guidance','Playbook and crosswalk resources'],['Web documents','PDF'],
 'No executable installation; use official resources',[], 'No integration API verified','None','None','Public reference website',[],['HTML','PDF','published crosswalk documents'],
 'US government reference material subject to NIST site terms; third-party material and trademarks retain their rights',
 'Official site accessible 2026-11-13; AI RMF 1.0 revision notice observed.',
 'Authoritative reference links and explicit framework identifiers in native records; no executable integration claim.',
 ['Reference updates require mapping review','Crosswalk does not imply certification'],source_url='https://airc.nist.gov')
add(13,'m3-framework','M3 Framework',4,'REFERENCE_RESOURCE','Official website and repository commit inspected; no executable stable release identified',
 ['Mount, Monitor, Manage methodology','SME governance guidance','Mappings and templates for multiple frameworks'],['Documentation','CSV/JSON/YAML artifacts described by licence'],
 'No install required for reference use; visit official site and repository',[], 'No application API verified','No SDK verified','No CLI verified','Static website and reference repository',[],['Methodology text','reference mappings','templates'],
 'CC-BY-4.0 standard text; Apache-2.0 code/data. Attribute Julius Gromyko and indicate changes. Trademarks reserved; no official-partner or M3-Certified claim.',
 'Official site and explicit 2026 licence grant verified. No executable interface demonstrated.',
 'Reference catalogue only. May evaluate separately versioned template import later with attribution.',
 ['Trademark/endorsement claims','Mapping completeness','Do not treat framework use as ISO certification'],source_url='https://m3framework.org')

for r in records:
    for f in extra:
        if (r['id']=='cdxgen' and '@cdxgen' in f['url']) or (r['id']=='riskforge' and '/riskforge/' in f['url']) or (r['id']=='opencomplai' and '/opencomplai-cli/' in f['url']) or (r['id']=='venturalitica' and '/venturalitica/' in f['url']) or (r['id']=='ai-atlas-nexus' and '/ai-atlas-nexus/' in f['url']) or (r['id']=='nist-airc' and 'airc.nist.gov' in f['url']) or (r['id']=='m3-framework' and 'm3framework.org' in f['url']) or (r['id']=='eu-ai-act-toolkit' and '@eu-ai-act' in f['url']):
            r['sources'].append({k:v for k,v in f.items() if k!='text'})
    if r['classification']=='REFERENCE_RESOURCE':r['test_status']='REFERENCE_VERIFIED_NOT_EXECUTABLE'
    if r['id']=='cdxgen':
        r['test_status']='REAL_EXECUTION_PASSED: 11 adapter/security tests; cdxgen 13.7.0 generated schema-validated CycloneDX 1.6 from an explicit npm v3 fixture; see docs/verification/cdxgen-test.json'
        r['installation']='cd integrations/tooling && npm ci --ignore-scripts --omit=optional; Node >=24.15, tested 24.22.3; lockfile pins cdxgen13.7.0 and patched glob14.0.6/minimatch11.0.8 overrides'
        r['integration_method']='Implemented restricted npm v3 lockfile CLI adapter. Node filesystem permissions deny child processes and addons; staged data only, no install scripts; background execution only.'
dest=ROOT/'docs/research'
(dest/'governance.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
lines=['# Governance and discovery upstream verification','', 'Inspected 2026-11-13. GitHub API returned 403 (shared anonymous rate limit); commit IDs were obtained using `git ls-remote` and files were read from commit-pinned raw URLs. Source hashes are in `sources/governance-source-manifest.json`. This register distinguishes verified interfaces from executed integrations. Raw inspection files remain in ignored `tmp/`; no third-party source is vendored.','', 'Current EU legal interpretation must use [Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) together with applicable amendments, including [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj), whose official EUR-Lex record was verified in force. Do not derive legal deadlines or certification claims from a toolkit README. ISO standard text is not reproduced.','']
for r in records:
    lines += [f"## {r['number']}. {r['name']}",'']
    for k,v in r.items():
        if k=='sources':
            lines += ['**Sources:** '+', '.join(f"[source {i+1}]({s['url']})" for i,s in enumerate(v)),'']
        elif k not in ('number','id','name'):
            lines += [f"**{k.replace('_',' ').capitalize()}:** "+('; '.join(v) if isinstance(v,list) else str(v)),'']
(dest/'governance.md').write_text('\n'.join(line.rstrip() for line in lines)+'\n',encoding='utf8')
manifest=[{**{k:v for k,v in r.items() if k!='files'},'files':[{k:v for k,v in f.items() if k!='text'} for f in r.get('files',[])]} for r in raw+[m3]]
(dest/'sources/governance-source-manifest.json').write_text(json.dumps({'inspected_at':'2026-11-13','repositories':manifest,'web_and_registry':[{k:v for k,v in f.items() if k!='text'} for f in extra]},indent=2)+'\n',encoding='utf8')
print(f'Wrote {len(records)} verified records')
