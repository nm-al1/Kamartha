"""Provision the Supabase profile: runtime role, migrations, grants, bucket.

Reads the SUPABASE_* tags in backend/.env. Prints status only; never prints
secrets. Aborts on an existing Kamartha schema unless --allow-existing is given.
"""
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'backend'
ENV_FILE = BACKEND / '.env'
ALLOWED_MIME = ['image/jpeg', 'image/png', 'application/pdf']
MAX_BYTES = 2 * 1024 * 1024

# TAG 3/4 in .env carries the Supabase profile. Map it to canonical names.
PROFILE_KEYS = {
    'ENVIRONMENT': 'SUPABASE_ENVIRONMENT',
    'APP_ORIGIN': 'SUPABASE_APP_ORIGIN',
    'MIGRATION_DATABASE_URL': 'SUPABASE_MIGRATION_DATABASE_URL',
    'DATABASE_URL': 'SUPABASE_DATABASE_URL',
    'SETUP_CODE_HASH': 'SUPABASE_SETUP_CODE_HASH',
    'IP_HASH_SECRET': 'SUPABASE_IP_HASH_SECRET',
    'SUPABASE_URL': 'SUPABASE_URL',
    'SUPABASE_SERVICE_KEY': 'SUPABASE_SERVICE_KEY',
    'STORAGE_BUCKET': 'STORAGE_BUCKET',
    'RUNTIME_ROLE': 'RUNTIME_ROLE',
}

REQUIRED = (
    'ENVIRONMENT',
    'APP_ORIGIN',
    'MIGRATION_DATABASE_URL',
    'DATABASE_URL',
    'RUNTIME_ROLE',
    'IP_HASH_SECRET',
    'SETUP_CODE_HASH',
    'SUPABASE_URL',
    'SUPABASE_SERVICE_KEY',
    'STORAGE_BUCKET',
)


class SetupError(RuntimeError):
    pass


def missing_keys(values):
    return [key for key in REQUIRED if not (values.get(key) or '').strip()]


def load_values():
    from dotenv import dotenv_values

    if not ENV_FILE.exists():
        raise SetupError(f'{ENV_FILE.name} tidak ditemukan.')
    raw = {key: (value or '').strip() for key, value in dotenv_values(ENV_FILE).items()}
    values = {name: raw.get(env_key, '') for name, env_key in PROFILE_KEYS.items()}
    values['RUNTIME_ROLE'] = values['RUNTIME_ROLE'] or 'kamartha_runtime'
    missing = missing_keys(values)
    if missing:
        shown = [PROFILE_KEYS.get(key, key) for key in missing]
        raise SetupError('Nilai berikut masih kosong di backend/.env: ' + ', '.join(shown))
    return values


def validate(values):
    from sqlalchemy.engine import make_url

    missing = missing_keys(values)
    if missing:
        raise SetupError('Nilai berikut masih kosong: ' + ', '.join(missing))
    owner = make_url(values['MIGRATION_DATABASE_URL'])
    runtime = make_url(values['DATABASE_URL'])
    for name, url in (('MIGRATION_DATABASE_URL', owner), ('DATABASE_URL', runtime)):
        if url.drivername != 'postgresql+psycopg':
            raise SetupError(f'{name} harus memakai postgresql+psycopg.')
        if url.host in (None, 'localhost', '127.0.0.1', '::1'):
            raise SetupError(f'{name} harus menunjuk host Supabase, bukan PostgreSQL lokal.')
        if url.query.get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
            raise SetupError(f'{name} harus memakai sslmode=require atau lebih ketat.')
        if not url.password:
            raise SetupError(f'{name} tidak memuat password.')
    owner_name = owner.username or ''
    if owner_name != 'postgres' and not owner_name.startswith('postgres.'):
        raise SetupError('MIGRATION_DATABASE_URL harus memakai akun postgres.')
    role = values['RUNTIME_ROLE']
    runtime_name = runtime.username or ''
    if runtime_name != role and not runtime_name.startswith(role + '.'):
        raise SetupError('DATABASE_URL harus memakai role runtime, bukan akun postgres.')
    base = values['SUPABASE_URL'].rstrip('/')
    if not base.startswith('https://') or '/rest/v1' in base or '/storage/v1' in base:
        raise SetupError('SUPABASE_URL harus https://<ref>.supabase.co tanpa path API.')
    import re
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,62}', values['STORAGE_BUCKET']):
        raise SetupError('STORAGE_BUCKET harus huruf kecil, angka, atau tanda hubung.')
    return owner, runtime, role, base


def ensure_role(engine, role, password):
    from psycopg import sql
    from sqlalchemy import text

    with engine.begin() as db:
        exists = db.scalar(
            text('SELECT 1 FROM pg_roles WHERE rolname = :role'), {'role': role})
        if exists:
            statement = sql.SQL('ALTER ROLE {} PASSWORD {}').format(
                sql.Identifier(role), sql.Literal(password))
            state = 'diperbarui'
        else:
            statement = sql.SQL(
                'CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD {}'
            ).format(sql.Identifier(role), sql.Literal(password))
            state = 'dibuat'
        db.exec_driver_sql(
            statement.as_string(db.connection.driver_connection))
    return state


def migrate_and_grant(engine, owner_url):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    os.environ['MIGRATION_DATABASE_URL'] = owner_url
    config = Config(str(BACKEND / 'alembic.ini'))
    config.set_main_option('script_location', str(BACKEND / 'migrations'))
    with engine.begin() as db:
        config.attributes['connection'] = db
        command.upgrade(config, 'head')
        db.exec_driver_sql((ROOT / 'ops' / 'grant_runtime.sql').read_text(encoding='utf-8'))
        revision = db.scalar(text('SELECT version_num FROM public.alembic_version'))
        tables = db.scalar(text(
            "SELECT count(*) FROM pg_tables WHERE schemaname = 'kamartha'"
        ))
    return revision, tables


def ensure_bucket(base, service_key, bucket):
    import httpx

    headers = {'Authorization': f'Bearer {service_key}', 'apikey': service_key}
    payload = {
        'id': bucket,
        'name': bucket,
        'public': False,
        'file_size_limit': MAX_BYTES,
        'allowed_mime_types': ALLOWED_MIME,
    }
    response = httpx.post(f'{base}/storage/v1/bucket', json=payload,
                          headers=headers, timeout=20)
    if response.status_code in (200, 201):
        return 'created'
    if response.status_code == 400 and 'exist' in response.text.lower():
        current = httpx.get(f'{base}/storage/v1/bucket/{bucket}', headers=headers, timeout=20)
        if current.status_code != 200:
            raise SetupError('Bucket sudah ada tetapi tidak dapat diperiksa.')
        if current.json().get('public') is not False:
            raise SetupError('Bucket sudah ada dan bersifat publik; hentikan dan periksa manual.')
        return 'exists'
    raise SetupError(f'Bucket gagal dibuat (HTTP {response.status_code}).')


def verify_runtime(runtime_url, engine):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.pool import NullPool

    runtime = create_engine(runtime_url, poolclass=NullPool, hide_parameters=True)
    try:
        with runtime.connect() as db:
            managers = db.scalar(text('SELECT count(*) FROM kamartha.managers'))
            can_create = db.scalar(text(
                "SELECT has_schema_privilege(current_user, 'kamartha', 'CREATE')"
            ))
        delete_denied = False
        try:
            with runtime.begin() as db:
                db.execute(text('DELETE FROM kamartha.attachments'))
        except DBAPIError as error:
            delete_denied = 'permission denied' in str(error).lower()
        with engine.connect() as db:
            exposed = db.scalar(text("""
                SELECT count(*) FROM pg_roles
                WHERE rolname IN ('anon', 'authenticated')
                  AND has_schema_privilege(rolname, 'kamartha', 'USAGE')
            """))
    finally:
        runtime.dispose()
    if managers != 0:
        raise SetupError('Tabel managers harus kosong pada project baru.')
    if can_create:
        raise SetupError('Runtime role masih memiliki hak CREATE pada schema kamartha.')
    if not delete_denied:
        raise SetupError('Runtime role masih dapat menghapus lampiran; periksa grant.')
    if exposed:
        raise SetupError('Role anon/authenticated masih memiliki akses ke schema kamartha.')
    return managers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-existing', action='store_true',
                        help='Lanjutkan walau schema kamartha sudah ada.')
    parser.add_argument('--skip-storage', action='store_true',
                        help='Lewati pembuatan bucket dan uji Storage.')
    args = parser.parse_args()

    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import NullPool

    values = load_values()
    owner_url, runtime_url, role, base = validate(values)
    engine = create_engine(owner_url.set(database='postgres'), poolclass=NullPool,
                           hide_parameters=True)
    checks = []
    try:
        with engine.connect() as db:
            existing = db.scalar(text("SELECT to_regclass('kamartha.managers') IS NOT NULL"))
        if existing and not args.allow_existing:
            raise SetupError(
                'Schema kamartha sudah ada. Project tidak kosong; ulangi dengan '
                '--allow-existing hanya bila ini memang project staging yang benar.'
            )
        checks.append(('project baru', 'lolos' if not existing else 'dilewati'))

        role_state = ensure_role(engine, role, runtime_url.password)
        checks.append((f'role {role}', role_state))

        revision, tables = migrate_and_grant(
            engine, owner_url.set(database='postgres').render_as_string(hide_password=False))
        checks.append(('migrasi', f'{revision} ({tables} tabel)'))
        checks.append(('grant runtime', 'lolos'))

        managers = verify_runtime(runtime_url.set(database='postgres'), engine)
        checks.append(('verifikasi runtime', f'lolos ({managers} manajer)'))

        if args.skip_storage:
            checks.append(('bucket', 'dilewati'))
        else:
            state = ensure_bucket(
                base, values['SUPABASE_SERVICE_KEY'], values['STORAGE_BUCKET'])
            checks.append((f"bucket {values['STORAGE_BUCKET']}", state + ' (privat)'))
    finally:
        engine.dispose()

    print('Provisioning Supabase selesai:')
    for name, state in checks:
        print(f'  - {name}: {state}')
    print('Langkah berikut: python ops/supabase_smoke.py')


if __name__ == '__main__':
    try:
        main()
    except SetupError as error:
        print(f'Setup dibatalkan: {error}', file=sys.stderr)
        raise SystemExit(1)
    except Exception as error:
        print(f'Setup gagal ({type(error).__name__}). Periksa koneksi dan tag SUPABASE_* di backend/.env; '
              'rincian tidak ditampilkan.', file=sys.stderr)
        raise SystemExit(1)
