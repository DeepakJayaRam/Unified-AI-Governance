"""Run one release gate, retaining output and exit code without printing secrets."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/release'


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    gate=sys.argv[1]
    env=dict(os.environ)
    cwd=ROOT
    node=ROOT/'tmp/tools/node-v24.22.3/node.exe'
    if node.exists():
        env['PATH']=str(node.parent)+os.pathsep+env['PATH']
        env['UAG_NODE_EXECUTABLE']=str(node)
    if gate=='backend-local':
        env['UAG_TEST_CDXGEN']='1'
        env['UAG_SCAN_TMP_ROOT']=tempfile.gettempdir()
        command=[sys.executable,'-m','pytest','-q','-ra']
    elif gate=='backend-services':
        command=['docker','compose','-f','docker-compose.yml','-f','docker-compose.presidio.yml',
                 'run','--rm','--no-deps','-v',str(ROOT/'tests')+':/app/tests:ro',
                 '-e','TEST_OPA_URL=http://opa:8181','-e','TEST_PRESIDIO_URL=http://presidio:8000',
                 '-e','UAG_TEST_CDXGEN=1','-e','UAG_SCAN_TMP_ROOT=/tmp','api','python','-m','pytest','-q','-ra','-p','no:cacheprovider','/app/tests']
    elif gate in ('frontend-unit','frontend-typecheck','frontend-format','frontend-build','browser'):
        cwd=ROOT/'frontend'
        if gate=='browser':
            credentials=json.loads((ROOT/'tmp/release-browser-credentials.json').read_text())
            env.update(E2E_EMAIL=credentials['email'],E2E_PASSWORD=credentials['password'], E2E_BASE_URL='http://127.0.0.1:3100')
            env.setdefault('E2E_SIGNING_ENABLED','1')
            if os.name=='nt' and Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe').is_file():
                env.setdefault('E2E_BROWSER_CHANNEL','msedge')
        script={'frontend-unit':'test','frontend-typecheck':'typecheck','frontend-format':'format:check','frontend-build':'build','browser':'test:e2e'}[gate]
        command=['npm.cmd' if os.name=='nt' else 'npm','run',script]
    else:
        raise SystemExit('Unknown gate')
    log=OUT/(gate+'.txt')
    if log.exists():
        archive=ROOT/'tmp/release-attempts'
        archive.mkdir(parents=True,exist_ok=True)
        (archive/f'{gate}-{time.time_ns()}.txt').write_bytes(log.read_bytes())
    with log.open('w',encoding='utf-8') as output:
        result=subprocess.run(command,cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT)
    print(log.read_text(encoding='utf-8')[-16000:])
    print(f'{gate}: exit {result.returncode}',flush=True)
    raise SystemExit(result.returncode)


if __name__=='__main__': main()
