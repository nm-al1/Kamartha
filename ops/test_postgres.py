"""Run pytest against a disposable, loopback-only PostgreSQL cluster.

Requires installed PostgreSQL binaries, not a running database or CREATEDB on
the application role. Existing application databases and .env are untouched.
"""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def serve_android_demo(url, backend):
    from alembic import command
    from alembic.config import Config
    from dotenv import dotenv_values
    import uvicorn

    sys.path.insert(0, str(backend))
    from app.core.config import Settings
    from app.core.security import hash_password
    from app.main import create_app

    setup_code = os.environ.get('KAMARTHA_ANDROID_SETUP_CODE') or dotenv_values(
        backend / '.env').get('LOCAL_SETUP_CODE')
    if not setup_code:
        raise RuntimeError('Siapkan KAMARTHA_ANDROID_SETUP_CODE secara privat.')
    database_url = url.render_as_string(hide_password=False)
    os.environ['MIGRATION_DATABASE_URL'] = database_url
    migration = Config(str(backend / 'alembic.ini'))
    migration.set_main_option('script_location', str(backend / 'migrations'))
    command.upgrade(migration, 'head')
    settings = Settings(
        _env_file=None, app_profile='local', local_environment='development',
        local_app_origin='http://127.0.0.1:8001', local_database_url=database_url,
        local_setup_code_hash=hash_password(setup_code), local_ip_hash_secret=secrets.token_urlsafe(32),
        supabase_url=None, supabase_service_key=None, whatsapp_enabled=False,
    )
    print('Android debug: API loopback 8001, PostgreSQL sekali pakai, WA nonaktif.', flush=True)
    uvicorn.run(create_app(settings), host='127.0.0.1', port=8001,
                log_level='warning', access_log=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pg-bin', type=Path, default=Path(
        os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\17\bin')))
    parser.add_argument('--restore-backup', type=Path,
                        help='Restore and verify a backup in this disposable cluster instead of pytest.')
    parser.add_argument('--flow-smoke', action='store_true',
                        help='Run business APIs with a new private Supabase test bucket; leaves primary DB untouched.')
    parser.add_argument('--android-demo', action='store_true',
                        help='Serve the USB debug API on loopback with a disposable database.')
    args, pytest_args = parser.parse_known_args()
    if sum((bool(args.restore_backup), args.flow_smoke, args.android_demo)) > 1:
        parser.error('Choose one of --restore-backup, --flow-smoke, or --android-demo.')
    from sqlalchemy.engine import URL
    from sqlalchemy import create_engine, text

    suffix = '.exe' if os.name == 'nt' else ''
    binaries = {name: args.pg_bin / (name + suffix) for name in ('initdb', 'pg_ctl')}
    if not all(path.is_file() for path in binaries.values()):
        parser.error('Set --pg-bin to the installed PostgreSQL bin directory.')
    backend = Path(__file__).resolve().parents[1] / 'backend'
    temp_parent = Path(os.environ.get('LOCALAPPDATA', tempfile.gettempdir()))
    if os.name == 'nt':
        temp_parent = temp_parent / 'Temp' / 'opencode'
        temp_parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='kamartha-tests-', dir=temp_parent))
    data, password_file = root / 'data', root / 'password'
    password = secrets.token_urlsafe(32)
    password_file.write_text(password, encoding='ascii')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]

    def run(name, *options):
        subprocess.run([str(binaries[name]), *map(str, options)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)

    started = False
    server = None
    try:
        run('initdb', '-D', data, '-U', 'postgres', '--auth=scram-sha-256',
            '--pwfile=' + str(password_file), '--encoding=UTF8', '--locale=C')
        password_file.unlink()
        start = subprocess.run(
            [str(binaries['pg_ctl']), '-D', str(data), '-l', str(root / 'postgres.log'),
             '-o', f'-h 127.0.0.1 -p {port}', '-w', 'start'],
            capture_output=True, text=True, timeout=60)
        if start.returncode:
            if os.name != 'nt' or 'could not create restricted token' not in start.stderr:
                start.check_returncode()
            # Some constrained Windows sessions cannot create pg_ctl's child token.
            with (root / 'postgres-direct.log').open('wb') as log:
                server = subprocess.Popen(
                    [str(args.pg_bin / 'postgres.exe'), '-D', str(data), '-h', '127.0.0.1',
                     '-p', str(port)], stdout=log, stderr=log)
            deadline = time.monotonic() + 30
            while True:
                if server.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError('Disposable PostgreSQL did not start.')
                ready = subprocess.run(
                    [str(args.pg_bin / 'pg_isready.exe'), '-h', '127.0.0.1', '-p', str(port),
                     '-t', '1', '-q'], timeout=5)
                if ready.returncode == 0:
                    break
                time.sleep(0.1)
        started = True
        url = URL.create('postgresql+psycopg', username='postgres', password=password,
                         host='127.0.0.1', port=port, database='postgres')
        engine = create_engine(url, isolation_level='AUTOCOMMIT', hide_parameters=True)
        try:
            with engine.connect() as db:
                db.execute(text('CREATE DATABASE kamartha_isolated_test'))
        finally:
            engine.dispose()
        if args.restore_backup:
            from backup import restore_database
            manifest = restore_database(url.set(database='kamartha_isolated_test'),
                                        args.restore_backup.resolve(), args.pg_bin)
            print(f"Isolated restore: PASS; {len(manifest['tables'])} tables; "
                  f"{len(manifest['objects'])} local Storage objects verified.")
            return 0
        if args.flow_smoke:
            from full_flow_smoke import run_live
            run_live(url.set(database='kamartha_isolated_test'))
            return 0
        if args.android_demo:
            serve_android_demo(url.set(database='kamartha_isolated_test'), backend)
            return 0
        env = os.environ.copy()
        env.update(APP_PROFILE='local', PYTHON_DOTENV_DISABLED='1',
                   CONFIRM_ISOLATED_TEST_DATABASE='yes',
                   TEST_DATABASE_URL=url.set(database='kamartha_isolated_test').render_as_string(
                       hide_password=False))
        return subprocess.run([sys.executable, '-m', 'pytest',
                               '--basetemp', str(root / 'pytest'), '-o', f'cache_dir={root / "pytest-cache"}',
                               *(pytest_args or ['tests', '-q', '--tb=short'])],
                              cwd=backend, env=env).returncode
    finally:
        try:
            if started:
                run('pg_ctl', '-D', data, '-m', 'fast', '-w', 'stop')
        finally:
            if server is not None:
                if server.poll() is None and not started:
                    server.terminate()
                server.wait(timeout=10)
            shutil.rmtree(root)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'Isolated PostgreSQL run failed ({type(error).__name__}).', file=sys.stderr)
        raise SystemExit(1)
