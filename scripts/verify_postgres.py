"""Real isolated PostgreSQL migration and raw-SQL RLS verification.

Uses an existing, verified portable binary distribution. Never modifies an
installed PostgreSQL service. Passwords are random, kept out of output, and
the temporary cluster stays within this repository's ignored tmp directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from urllib.parse import quote

import psycopg
from psycopg import sql

ROOT=Path(__file__).resolve().parents[1]
PORT=15439


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bin-dir',default=str(ROOT/'tmp/tools/pg18/pgsql/bin'))
    args=parser.parse_args()
    bin_dir=Path(args.bin_dir).resolve()
    for name in ('postgres.exe','initdb.exe','pg_ctl.exe'):
        if not (bin_dir/name).is_file():raise SystemExit(f'Portable PostgreSQL binary missing: {name}')
    with socket.socket() as probe:
        try:probe.bind(('127.0.0.1',PORT))
        except OSError:raise SystemExit('Isolated validation port15439 is in use; no existing process touched')
    workspace=ROOT/'tmp'/('postgres-validation-'+secrets.token_hex(6))
    workspace.mkdir(parents=True)
    data_dir=workspace/'data'
    assert data_dir.resolve().is_relative_to((ROOT/'tmp').resolve())
    password=secrets.token_urlsafe(30)
    app_password=secrets.token_urlsafe(30)
    admin='uag_verify_admin'
    app='uag_verify_app'
    env={**os.environ,'TEMP':str(workspace),'TMP':str(workspace),'PGCONNECT_TIMEOUT':'5'}
    pwfile=workspace/'initial-password.txt'
    report={'verified_at':'2026-11-13','scope':'Real PostgreSQL engine, isolated loopback-only port15439, synthetic records only',
            'tests':{},'commands':[],'status':'failed'}
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    started=False

    def redact(value):
        return value.replace(password,'<redacted>').replace(app_password,'<redacted>')

    def run(command,label,timeout=60,override=None):
        # A Windows postgres child can inherit pg_ctl's output handles. Regular
        # files avoid waiting forever for pipe EOF after pg_ctl itself exits.
        stdout_path=workspace/f'command-{len(report["commands"])}.out'
        stderr_path=workspace/f'command-{len(report["commands"])}.err'
        with stdout_path.open('w',encoding='utf8') as stdout,stderr_path.open('w',encoding='utf8') as stderr:
            process=subprocess.run(command,cwd=ROOT,env=override or env,stdout=stdout,stderr=stderr,text=True,timeout=timeout,creationflags=flags)
        output=stdout_path.read_text(encoding='utf8',errors='replace')
        errors=stderr_path.read_text(encoding='utf8',errors='replace')
        report['commands'].append({'command':label,'exit_code':process.returncode,'stdout':redact(output[-4000:]),'stderr':redact(errors[-4000:])})
        if process.returncode:raise RuntimeError(f'{label} failed: '+redact(errors[-1000:]))
        return output

    def connect(user=admin,credential=password):
        return psycopg.connect(host='127.0.0.1',port=PORT,dbname='postgres',user=user,password=credential,autocommit=True)

    try:
        report['version']=run([str(bin_dir/'postgres.exe'),'--version'],'postgres --version').strip()
        report['postgres_binary_sha256']=hashlib.sha256((bin_dir/'postgres.exe').read_bytes()).hexdigest()
        download=ROOT/'tmp/tools/pg18/download.json'
        if download.exists():report['distribution']=json.loads(download.read_text())
        pwfile.write_text(password+'\n',encoding='utf8')
        try:
            run([str(bin_dir/'initdb.exe'),'-D',str(data_dir),'-U',admin,'--auth=scram-sha-256','--pwfile='+str(pwfile),'--encoding=UTF8','--locale=C'],
                'initdb -D <isolated-data> -U <test-admin> --auth=scram-sha-256 --pwfile=<ephemeral-file> --encoding=UTF8 --locale=C')
        finally:
            if pwfile.exists():pwfile.unlink()
        run([str(bin_dir/'pg_ctl.exe'),'-D',str(data_dir),'-l',str(workspace/'server.log'),'-o',f'-p {PORT} -h 127.0.0.1','-w','start'],
            'pg_ctl -D <isolated-data> -l <isolated-log> -o "-p15439 -h127.0.0.1" -w start')
        started=True
        migration_env={**env,'DATABASE_URL':f'postgresql+psycopg://{admin}:{quote(password)}@127.0.0.1:{PORT}/postgres'}
        run([sys.executable,'-m','alembic','upgrade','head'],'alembic upgrade head (isolated PostgreSQL)',override=migration_env)
        report['tests']['migration_upgrade']='passed'
        with connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS').format(sql.Identifier(app),sql.Literal(app_password)))
                cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA public TO {}').format(sql.Identifier(app)))
                cursor.execute(sql.SQL('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}').format(sql.Identifier(app)))
                cursor.execute("INSERT INTO tenants(id,name) VALUES ('tenant-a','Synthetic A'),('tenant-b','Synthetic B')")
                cursor.execute("INSERT INTO records(id,tenant_id,kind,data,created_at,updated_at) VALUES ('a-record','tenant-a','systems','{}',now(),now()),('b-record','tenant-b','systems','{}',now(),now())")
                cursor.execute("INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_id,details,previous_hash,event_hash,created_at) VALUES ('a-audit','tenant-a','actor','test','a-record','{}','0','1',now()),('b-audit','tenant-b','actor','test','b-record','{}','0','2',now())")
                cursor.execute("SELECT tablename,rowsecurity FROM pg_tables WHERE schemaname='public' AND tablename IN ('records','audit_events') ORDER BY tablename")
                assert cursor.fetchall()==[('audit_events',True),('records',True)]
                cursor.execute("SELECT relname,relforcerowsecurity FROM pg_class WHERE relname IN ('records','audit_events') ORDER BY relname")
                assert cursor.fetchall()==[('audit_events',True),('records',True)]
                report['tests']['rls_enabled_and_forced']='passed'
        with connect(app,app_password) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user')
                assert cursor.fetchone()==(False,False)
                report['tests']['non_superuser_without_bypassrls']='passed'
                cursor.execute('SELECT count(*) FROM records')
                assert cursor.fetchone()[0]==0
                cursor.execute('SELECT count(*) FROM audit_events')
                assert cursor.fetchone()[0]==0
                report['tests']['no_tenant_context_reads_zero_rows']='passed'
                cursor.execute("SELECT set_config('app.tenant_id','tenant-a',false)")
                cursor.execute('SELECT id FROM records')
                assert cursor.fetchall()==[('a-record',)]
                cursor.execute('SELECT id FROM audit_events')
                assert cursor.fetchall()==[('a-audit',)]
                report['tests']['raw_sql_cross_tenant_select_isolated']='passed'
                for table,statement in [
                    ('records',"INSERT INTO records(id,tenant_id,kind,data,created_at,updated_at) VALUES ('forbidden','tenant-b','systems','{}',now(),now())"),
                    ('audit_events',"INSERT INTO audit_events(id,tenant_id,actor_id,action,resource_id,details,previous_hash,event_hash,created_at) VALUES ('forbidden','tenant-b','actor','test','b-record','{}','0','1',now())")]:
                    try:cursor.execute(statement)
                    except psycopg.errors.InsufficientPrivilege:report['tests'][f'raw_sql_cross_tenant_{table}_insert_denied']='passed'
                    else:raise AssertionError(f'Cross-tenant {table} insertion unexpectedly succeeded')
                cursor.execute("UPDATE records SET data='{\"changed\":true}' WHERE id='b-record'")
                assert cursor.rowcount==0
                report['tests']['raw_sql_cross_tenant_update_changes_zero']='passed'
                try:cursor.execute("UPDATE records SET tenant_id='tenant-b' WHERE id='a-record'")
                except psycopg.errors.InsufficientPrivilege:report['tests']['raw_sql_tenant_reassignment_denied']='passed'
                else:raise AssertionError('Cross-tenant reassignment unexpectedly succeeded')
                for action in ('UPDATE','DELETE'):
                    statement="UPDATE audit_events SET action='tampered' WHERE id='a-audit'" if action=='UPDATE' else "DELETE FROM audit_events WHERE id='a-audit'"
                    try:cursor.execute(statement)
                    except psycopg.errors.RaiseException as error:
                        assert 'append-only' in str(error)
                        report['tests'][f'audit_{action.lower()}_denied_by_trigger']='passed'
                    else:raise AssertionError(f'Audit {action} unexpectedly succeeded')
                cursor.execute("SELECT set_config('app.tenant_id','tenant-b',false)")
                cursor.execute('SELECT id FROM records')
                assert cursor.fetchall()==[('b-record',)]
                report['tests']['tenant_b_context_reads_only_b']='passed'
        run([sys.executable,'-m','alembic','downgrade','base'],'alembic downgrade base (isolated PostgreSQL)',override=migration_env)
        run([sys.executable,'-m','alembic','upgrade','head'],'alembic upgrade head after downgrade (isolated PostgreSQL)',override=migration_env)
        report['tests']['migration_down_up']='passed'
        report['status']='passed'
        report['limitations']=['The app database role can set app.tenant_id; authenticated API and trusted worker context remain the security boundary against arbitrary SQL access.',
            'Migration owner/superuser is intentionally separate; database superusers can bypass RLS and modify triggers.',
            'This verifies migrations and record/audit RLS only; it does not claim full PostgreSQL API load or cloud validation.']
    except Exception as error:
        report['error']=redact(str(error))
    finally:
        if started:
            try:
                run([str(bin_dir/'pg_ctl.exe'),'-D',str(data_dir),'-m','fast','-w','stop'],'pg_ctl -D <isolated-data> -m fast -w stop')
                report['server_stopped']=True
            except Exception as error:report['stop_error']=redact(str(error))
        destination=ROOT/'docs/validation/postgres.json'
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
    if report['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
