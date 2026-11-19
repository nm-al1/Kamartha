"""Run an isolated local demo without resetting any existing database."""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
sys.path.insert(0, str(BACKEND))


def validate_database(name, allow_test=False):
    if allow_test and name == 'kamartha_test':
        return name
    if not re.fullmatch(r'kamartha_demo(?:_[a-z0-9]+)*', name):
        raise ValueError('Nama database demo harus diawali kamartha_demo.')
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='kamartha_demo')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--allow-test-database', action='store_true',
                        help='Izinkan kamartha_test hanya bila kosong dan tidak ada data.')
    parser.add_argument('--reuse-test-database', action='store_true',
                        help='Pakai ulang kamartha_test yang sudah berisi akun demo.')
    parser.add_argument('--origin', default='http://localhost:8080',
                        help='Origin frontend yang diizinkan, misalnya http://localhost:8081.')
    args = parser.parse_args()
    if args.reuse_test_database and not args.allow_test_database:
        raise ValueError('--reuse-test-database memerlukan --allow-test-database.')
    database = validate_database(
        args.database, args.allow_test_database or args.reuse_test_database)
    if not 1024 <= args.port <= 65535:
        raise ValueError('Port demo tidak sah.')

    from alembic import command
    from alembic.config import Config
    from dotenv import dotenv_values
    from psycopg import sql
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool
    import uvicorn

    from app.core.config import Settings
    from app.core.security import hash_password
    from app.main import create_app

    values = dotenv_values(BACKEND / '.env')
    owner = make_url(values['LOCAL_MIGRATION_DATABASE_URL'])
    runtime = make_url(values['LOCAL_DATABASE_URL'])
    if owner.host not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Demo hanya boleh memakai PostgreSQL lokal.')
    if (runtime.host not in ('localhost', '127.0.0.1', '::1')
            or (runtime.port or 5432) != (owner.port or 5432)):
        raise ValueError('Host dan port runtime harus sama dengan database lokal pemilik.')
    if runtime.username != 'kamartha_runtime':
        raise ValueError('Demo memerlukan role kamartha_runtime yang sudah dikonfigurasi.')

    admin = create_engine(owner.set(database='postgres'), isolation_level='AUTOCOMMIT',
                          poolclass=NullPool, hide_parameters=True)
    try:
        with admin.connect() as db:
            exists = db.scalar(text('SELECT 1 FROM pg_database WHERE datname=:name'), {'name': database})
            if database == 'kamartha_test':
                if not exists:
                    raise ValueError('Database kamartha_test tidak ditemukan.')
            elif not exists:
                db.exec_driver_sql(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)).as_string())
    finally:
        admin.dispose()

    engine = create_engine(owner.set(database=database), poolclass=NullPool, hide_parameters=True)
    if database == 'kamartha_test' and not args.reuse_test_database:
        try:
            with engine.connect() as db:
                run_tables = db.scalar(text("""
                    SELECT count(*) FROM pg_tables
                    WHERE schemaname='public' AND tablename <> 'alembic_version'
                """))
                has_managers = db.scalar(text(
                    "SELECT to_regclass('kamartha.managers') IS NOT NULL"))
                managers = db.scalar(text('SELECT count(*) FROM kamartha.managers')) if has_managers else 0
                if run_tables or managers:
                    raise ValueError('kamartha_test berisi data; demo tidak akan menghapus data.')
        finally:
            engine.dispose()
        engine = create_engine(owner.set(database=database), poolclass=NullPool, hide_parameters=True)

    engine = create_engine(owner.set(database=database), poolclass=NullPool, hide_parameters=True)
    try:
        with engine.begin() as db:
            os.environ['MIGRATION_DATABASE_URL'] = owner.set(database=database).render_as_string(hide_password=False)
            config = Config(str(BACKEND / 'alembic.ini'))
            config.set_main_option('script_location', str(BACKEND / 'migrations'))
            config.attributes['connection'] = db
            command.upgrade(config, 'head')
            db.exec_driver_sql((ROOT / 'ops' / 'grant_runtime.sql').read_text(encoding='utf-8'))
            accounts = db.scalar(text('SELECT count(*) FROM kamartha.managers'))
    finally:
        engine.dispose()

    code = values.get('LOCAL_SETUP_CODE')
    ip_secret = values.get('LOCAL_IP_HASH_SECRET')
    if not code or not ip_secret or len(ip_secret) < 32:
        raise ValueError('LOCAL_SETUP_CODE dan LOCAL_IP_HASH_SECRET wajib ada di backend/.env.')

    settings = Settings(
        _env_file=None, app_profile='local', environment='development',
        app_origin=args.origin,
        database_url=runtime.set(database=database).render_as_string(hide_password=False),
        setup_code_hash=hash_password(code), ip_hash_secret=ip_secret,
        supabase_url=None, supabase_service_key=None,
    )
    print(f'Demo database: {database}; accounts: {accounts}', flush=True)
    print(f'Kode setup lokal: baca LOCAL_SETUP_CODE di backend/.env', flush=True)
    print(f'API: http://localhost:{args.port}/api/v1; frontend: {args.origin}', flush=True)
    print('Local demo only. Attachments use temporary FakeStorage. No database is reset.', flush=True)
    uvicorn.run(create_app(settings), host='127.0.0.1', port=args.port,
                log_level='warning', access_log=False)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Demo gagal dimulai ({type(error).__name__}). Periksa PostgreSQL lokal dan backend/.env; '
              'rincian koneksi tidak ditampilkan.', file=sys.stderr)
        raise SystemExit(1)
