"""Restricted npm lockfile inventory using the genuine pinned cdxgen CLI.

This adapter accepts data, never a host path or a shell command. It does not
install dependencies or scan arbitrary repositories. Production execution
still requires the documented container resource and egress boundaries.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from integrations.base import AdapterResult, ExecutionError, safe_run

TOOL_ROOT = Path(__file__).resolve().parent / 'tooling'
CDXGEN_ROOT = TOOL_ROOT / 'node_modules' / '@cdxgen' / 'cdxgen'
NAME = re.compile(r'^(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*$')
VERSION_RANGE = re.compile(r'^[0-9A-Za-z.*^~<>=| +_-]{1,120}$')
MAX_INPUT_BYTES = 1_000_000
MAX_OUTPUT_BYTES = 8_000_000


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _dependencies(value: object) -> None:
    if not isinstance(value, dict) or len(value) > 2000:
        raise ValueError('Dependency map must contain at most 2000 entries')
    for name, spec in value.items():
        if not NAME.fullmatch(name) or not isinstance(spec, str) or not VERSION_RANGE.fullmatch(spec):
            raise ValueError('Only registry package names and version ranges are supported')


def validate_scan_input(data: dict) -> tuple[dict, dict]:
    if not isinstance(data, dict) or set(data) != {'package_json', 'package_lock'}:
        raise ValueError('Provide package_json and package_lock JSON objects only')
    if len(_json_bytes(data)) > MAX_INPUT_BYTES:
        raise ValueError('Manifest input exceeds 1 MB')
    manifest, lock = data['package_json'], data['package_lock']
    if not isinstance(manifest, dict) or not isinstance(lock, dict):
        raise ValueError('Both manifests must be JSON objects')
    allowed_manifest = {'name','version','description','license','private','dependencies',
                        'devDependencies','optionalDependencies','peerDependencies','engines'}
    if set(manifest) - allowed_manifest:
        raise ValueError('Manifest contains unsupported fields; remove scripts, configuration and workspaces')
    if not isinstance(manifest.get('name'), str) or not NAME.fullmatch(manifest['name']):
        raise ValueError('A valid registry package name is required')
    if not isinstance(manifest.get('version'), str) or not VERSION_RANGE.fullmatch(manifest['version']):
        raise ValueError('A package version is required')
    for key in ('description','license'):
        if key in manifest and (not isinstance(manifest[key],str) or len(manifest[key])>5000):
            raise ValueError('Description and licence must be bounded strings')
    if 'private' in manifest and not isinstance(manifest['private'],bool):
        raise ValueError('private must be a boolean')
    for key in ('dependencies','devDependencies','optionalDependencies','peerDependencies'):
        if key in manifest:
            _dependencies(manifest[key])
    if set(lock) - {'name','version','lockfileVersion','requires','packages'}:
        raise ValueError('Only npm lockfile version 3 package inventories are supported')
    if type(lock.get('lockfileVersion')) is not int or lock['lockfileVersion'] != 3:
        raise ValueError('package_lock must use lockfileVersion 3')
    packages = lock.get('packages')
    if not isinstance(packages, dict) or not packages or len(packages) > 2000 or '' not in packages:
        raise ValueError('Lockfile requires a root package and at most 2000 packages')
    allowed_package = {'name','version','license','resolved','integrity','dev','optional',
                       'devOptional','inBundle','hasInstallScript','dependencies','devDependencies',
                       'optionalDependencies','peerDependencies','peerDependenciesMeta','engines',
                       'os','cpu','funding','bin'}
    for path, package in packages.items():
        if path:
            parts = path.split('node_modules/')
            if parts[0] != '' or any(not NAME.fullmatch(p.rstrip('/')) for p in parts[1:]):
                raise ValueError('Lockfile package paths must remain under node_modules')
        if not isinstance(package, dict) or set(package) - allowed_package:
            raise ValueError('Lockfile package contains unsupported fields or local links')
        if 'version' in package and (not isinstance(package['version'],str) or not VERSION_RANGE.fullmatch(package['version'])):
            raise ValueError('Invalid lockfile package version')
        for key in ('dependencies','devDependencies','optionalDependencies','peerDependencies'):
            if key in package:
                _dependencies(package[key])
        if 'resolved' in package:
            if not isinstance(package['resolved'],str):
                raise ValueError('Invalid resolved package URL')
            url = urlsplit(package['resolved'])
            if url.scheme != 'https' or url.hostname != 'registry.npmjs.org' or url.username or url.password or url.port not in (None,443):
                raise ValueError('Only HTTPS registry.npmjs.org resolved URLs are accepted')
    if packages[''].get('name') != manifest['name'] or packages[''].get('version') != manifest['version']:
        raise ValueError('Manifest and lockfile root name/version must match')
    for key in ('dependencies','devDependencies','optionalDependencies','peerDependencies'):
        if packages[''].get(key,{}) != manifest.get(key,{}):
            raise ValueError('Manifest and lockfile root dependency maps must match')
    return manifest, lock


def _node() -> str:
    candidate = os.environ.get('UAG_NODE_EXECUTABLE') or shutil.which('node')
    if not candidate or not Path(candidate).is_absolute() or not Path(candidate).is_file():
        raise ValueError('A supported Node executable must be configured by the deployment')
    return str(Path(candidate).resolve())


def _scan_root() -> Path:
    configured=os.environ.get('UAG_SCAN_TMP_ROOT')
    root=Path(configured or tempfile.gettempdir())
    if not root.is_absolute() or not root.is_dir() or any(char.isspace() for char in str(root)):
        raise ValueError('Set UAG_SCAN_TMP_ROOT to an existing absolute directory without spaces; cdxgen secure mode requires this')
    return root.resolve()


def _environment(directory: Path, node: str) -> dict[str,str]:
    # Never inherit credential variables, NODE_OPTIONS, npm configuration or proxies.
    result = {key: os.environ[key] for key in ('SystemRoot','WINDIR','COMSPEC','PATHEXT') if key in os.environ}
    result.update({'PATH':str(Path(node).parent), 'HOME':str(directory), 'USERPROFILE':str(directory),
                   'TEMP':str(directory), 'TMP':str(directory), 'TMPDIR':str(directory),
                   'NO_COLOR':'1', 'CDXGEN_SECURE_MODE':'true', 'CDXGEN_ALLOWED_HOSTS':'invalid.local',
                   'CDXGEN_ALLOWED_PATHS':str(directory), 'CDXGEN_TEMP_DIR':str(directory/'temp'),
                   'FETCH_LICENSE':'false', 'CDXGEN_NO_PROGRESS':'true', 'CDXGEN_LOG_LEVEL':'silent'})
    return result


class CdxgenAdapter:
    id = 'cdxgen'
    version = '13.7.0'
    capabilities = ['npm_lockfile_inventory','cyclonedx_1_6','advisory_discovery']

    def validate_config(self, config: dict) -> dict:
        if not isinstance(config,dict) or set(config) - {'timeout_seconds'}:
            raise ValueError('Supported cdxgen configuration: timeout_seconds only')
        timeout = config.get('timeout_seconds',60)
        if type(timeout) not in (int,float) or not 1 <= timeout <= 120:
            raise ValueError('timeout_seconds must be between 1 and 120')
        return {'timeout_seconds':timeout}

    def health(self, config: dict) -> dict:
        try:
            self.validate_config(config)
            try:
                _scan_root()
            except ValueError as error:
                return {'status':'not_configured','detail':str(error)}
            package_file=CDXGEN_ROOT/'package.json'
            if not package_file.is_file():
                return {'status':'not_configured','detail':'Install pinned discovery tooling using npm ci --ignore-scripts --omit=optional'}
            if json.loads(package_file.read_text(encoding='utf8')).get('version') != self.version:
                return {'status':'failed','detail':'Installed cdxgen version does not match the tested pin'}
            node=_node()
            result=safe_run([node,'--version'],cwd=TOOL_ROOT,env=_environment(TOOL_ROOT,node),timeout=10,max_output=1024)
            match=re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)\s*',result.stdout)
            if result.returncode or not match or tuple(map(int,match.groups())) < (24,15,0):
                return {'status':'not_configured','detail':'Node >=24.15.0 required; tested with 24.22.3'}
            return {'status':'connected','detail':f'cdxgen {self.version}; {result.stdout.strip()}'}
        except (ValueError,OSError,ExecutionError,json.JSONDecodeError):
            return {'status':'failed','detail':'Discovery tooling health check failed'}

    def execute(self, input: dict, config: dict,
                cancelled: Callable[[],bool] = lambda:False) -> AdapterResult:
        try:
            checked=self.validate_config(config)
            manifest,lock=validate_scan_input(input)
            if cancelled():
                raise ExecutionError('cancelled')
            if self.health(config)['status'] != 'connected':
                raise ExecutionError('not_configured')
            node=_node()
            with tempfile.TemporaryDirectory(prefix='uag-cdxgen-',dir=_scan_root()) as temporary:
                directory=Path(temporary).resolve()
                for filename,data in (('package.json',manifest),('package-lock.json',lock)):
                    (directory/filename).write_bytes(_json_bytes(data))
                output=directory/'bom.json'
                argv=[node,'--permission',f'--allow-fs-read={TOOL_ROOT.resolve()}',
                      f'--allow-fs-read={directory}',f'--allow-fs-write={directory}',
                      str(CDXGEN_ROOT/'bin/cdxgen-secure.js'),'-t','js',
                      '--no-install-deps','--no-babel','--no-recurse','--no-rust',
                      '--no-include-formulation','--no-cache','--spec-version','1.6',
                      '--output',str(output),str(directory)]
                result=safe_run(argv,cwd=directory,env=_environment(directory,node),
                                timeout=checked['timeout_seconds'],max_output=500_000,cancelled=cancelled)
                if result.returncode or not output.is_file():
                    return AdapterResult(status='failed',raw_output={'stdout':result.stdout,'stderr':result.stderr},
                                         error={'code':'upstream_failed','message':'cdxgen did not produce an accepted BOM'},
                                         provenance={'tool':self.id,'version':self.version,'elapsed_ms':result.elapsed_ms})
                if output.stat().st_size > MAX_OUTPUT_BYTES:
                    raise ExecutionError('output_limit_exceeded')
                raw=output.read_bytes()
                bom=json.loads(raw)
                if bom.get('bomFormat') != 'CycloneDX' or bom.get('specVersion') != '1.6' or not isinstance(bom.get('components'),list):
                    raise ExecutionError('unexpected_output_format')
                components=[{key:item[key] for key in ('type','group','name','version','purl','licenses') if key in item}
                            for item in bom['components']]
                findings=[]
                for component in components:
                    if not component.get('licenses'):
                        findings.append({'title':f"Licence metadata missing: {component.get('name','component')}",
                                         'severity':'info','rule_id':'inventory.missing_license',
                                         'description':'Inventory metadata does not include a licence. Review upstream terms; no violation is inferred.'})
                if cancelled():
                    raise ExecutionError('cancelled')
                return AdapterResult(status='succeeded',raw_output={'bom':bom,'bom_text':raw.decode('utf-8'),'stdout':result.stdout,'stderr':result.stderr},
                    normalized={'format':'CycloneDX','spec_version':'1.6','bom':bom,'components':components,'component_count':len(components),
                                'findings':findings,'limitations':['Lockfile inventory only; no installed tree or source usage analysis',
                                                               'Not a vulnerability scan, full AI discovery or legal licence determination']},
                    provenance={'tool':self.id,'version':self.version,'elapsed_ms':result.elapsed_ms,
                                'input_sha256':hashlib.sha256(_json_bytes(input)).hexdigest(),
                                'artifact_sha256':hashlib.sha256(raw).hexdigest(),
                                'execution_mode':'restricted npm lockfile; Node permissions; no child processes; no dependency installation',
                                'command':['node']+[argument.replace(str(TOOL_ROOT.resolve()),'<tooling>').replace(str(directory),'<staging>') for argument in argv[1:]],
                                'configuration':checked},
                    logs=[f'cdxgen finished with {len(components)} inventory components; validation enabled'])
        except ValueError as error:
            return AdapterResult(status='failed',error={'code':'invalid_input','message':str(error)})
        except (ExecutionError,OSError,json.JSONDecodeError) as error:
            code=str(error) if isinstance(error,ExecutionError) else 'execution_failed'
            return AdapterResult(status='failed',error={'code':code,'message':'Discovery execution failed; inspect configuration and worker availability'})


ADAPTERS={'cdxgen':CdxgenAdapter()}
