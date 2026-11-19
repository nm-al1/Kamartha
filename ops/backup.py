"""Back up Kamartha PostgreSQL and private Storage; restore only to empty local test databases."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote, urlsplit
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


class BackupError(RuntimeError):
    pass


def file_digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def protect_directory(directory):
    if os.name == 'nt':
        user = os.environ.get('USERNAME')
        domain = os.environ.get('USERDOMAIN')
        if not user or not domain:
            raise BackupError('Cannot identify the local backup owner.')
        result = subprocess.run(['icacls.exe', str(directory), '/inheritance:r',
                                 '/grant:r', f'{domain}\\{user}:(OI)(CI)F'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=20)
        if result.returncode:
            raise BackupError('Cannot restrict backup directory permissions.')
    else:
        directory.chmod(0o700)


def verify_file(path, expected):
    if not Path(path).is_file() or file_digest(path) != expected:
        raise BackupError('Backup checksum mismatch or missing file.')


def blob_path(directory, key):
    return Path(directory) / 'objects' / hashlib.sha256(key.encode('utf-8')).hexdigest()


def validate_restore_target(url):
    url = make_url(url)
    if (url.drivername != 'postgresql+psycopg'
            or url.host not in ('127.0.0.1', 'localhost', '::1')
            or not (url.database or '').endswith('_test')):
        raise BackupError('Restore requires a loopback PostgreSQL database ending in _test.')
    return url


def pg_run(pg_bin, tool, url, *options):
    url = make_url(url)
    executable = Path(pg_bin) / (tool + ('.exe' if os.name == 'nt' else ''))
    env = {key: value for key, value in os.environ.items() if not key.startswith('PG')}
    env.update(PGHOST=url.host or 'localhost', PGPORT=str(url.port or 5432),
               PGDATABASE=url.database or '', PGUSER=url.username or '',
               PGPASSWORD=url.password or '', PGCONNECT_TIMEOUT='15',
               PGSSLMODE=url.query.get('sslmode', 'prefer'), PGAPPNAME='kamartha-backup')
    result = subprocess.run([str(executable), '--no-password', *map(str, options)],
                            env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        # PostgreSQL diagnostics may contain connection details; never echo them.
        raise BackupError(f'{tool} failed; no connection details printed.')


def table_fingerprints(db):
    names = db.execute(text("""
        SELECT tablename FROM pg_tables WHERE schemaname='kamartha' ORDER BY tablename
    """)).scalars().all()
    result = {}
    for name in names:
        identifier = db.dialect.identifier_preparer.quote_identifier(name)
        digest, count = hashlib.sha256(), 0
        rows = db.execute(text(
            f'SELECT row_to_json(t)::text FROM kamartha.{identifier} t '
            'ORDER BY row_to_json(t)::text COLLATE "C"'))
        for row in rows:
            encoded = row[0].encode('utf-8')
            digest.update(len(encoded).to_bytes(8, 'big'))
            digest.update(encoded)
            count += 1
        result[name] = {'rows': count, 'sha256': digest.hexdigest()}
    return result


class BucketReader:
    def __init__(self, base, key, bucket):
        import httpx
        parsed = urlsplit(base)
        if (parsed.scheme != 'https' or not parsed.hostname
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise BackupError('Storage backup requires an HTTPS origin without credentials or API paths.')
        self.client = httpx.Client(base_url=base.rstrip('/') + '/storage/v1/',
                                   headers={'apikey': key, 'Authorization': f'Bearer {key}'},
                                   timeout=30)
        self.bucket = quote(bucket, safe='')

    def close(self):
        self.client.close()

    def list_keys(self):
        pending, keys, visited = [''], [], set()
        while pending:
            prefix = pending.pop()
            if prefix in visited:
                raise BackupError('Storage listing repeated a folder.')
            visited.add(prefix)
            offset = 0
            while True:
                response = self.client.post(f'object/list/{self.bucket}', json={
                    'prefix': prefix, 'limit': 100, 'offset': offset,
                    'sortBy': {'column': 'name', 'order': 'asc'}})
                if response.status_code != 200 or not isinstance(response.json(), list):
                    raise BackupError('Storage listing failed.')
                rows = response.json()
                for row in rows:
                    name = row.get('name')
                    if not isinstance(name, str) or not name or '/' in name or name in ('.', '..'):
                        raise BackupError('Storage listing contained an invalid name.')
                    key = prefix + name
                    if row.get('id') is None:
                        pending.append(key + '/')
                    else:
                        keys.append(key)
                if len(rows) < 100:
                    break
                offset += 100
        if len(keys) != len(set(keys)):
            raise BackupError('Storage listing contained duplicate objects.')
        return sorted(keys)

    def get(self, key):
        response = self.client.get(f'object/{self.bucket}/{quote(key, safe="/")}',
                                   params={'v': uuid4().hex})
        if response.status_code != 200:
            raise BackupError('Storage object download failed.')
        if len(response.content) > 2 * 1024 * 1024:
            raise BackupError('Storage object exceeds the configured 2 MB limit.')
        return response.content


def create_backup(url, storage, destination, pg_bin):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    protect_directory(destination)
    (destination / 'objects').mkdir()
    engine = create_engine(url, hide_parameters=True, connect_args={'connect_timeout': 15})
    try:
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as db, db.begin():
            db.execute(text("SET LOCAL lock_timeout='10s'"))
            db.execute(text("SET LOCAL timezone='UTC'"))
            db.execute(text("SET LOCAL datestyle='ISO, YMD'"))
            tables = db.execute(text("""
                SELECT tablename FROM pg_tables WHERE schemaname='kamartha' ORDER BY tablename
            """)).scalars().all()
            if not tables:
                raise BackupError('Kamartha schema is missing.')
            identifiers = [
                'kamartha.' + db.dialect.identifier_preparer.quote_identifier(name) for name in tables]
            db.execute(text('LOCK TABLE ' + ', '.join(identifiers + ['public.alembic_version']) + ' IN SHARE MODE'))
            snapshot = db.scalar(text('SELECT pg_export_snapshot()'))
            manifest = {'format': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                        'revision': db.scalar(text('SELECT version_num FROM public.alembic_version')),
                        'tables': table_fingerprints(db), 'dumps': {}, 'objects': []}
            for filename, selector in [('database.dump', ['--schema=kamartha']),
                                       ('revision.dump', ['--table=public.alembic_version'])]:
                pg_run(pg_bin, 'pg_dump', url, '--format=custom', '--no-owner', '--no-privileges',
                       '--snapshot=' + snapshot, '--lock-wait-timeout=10000',
                       '--file=' + str(destination / filename), *selector)
                manifest['dumps'][filename] = file_digest(destination / filename)
            for key in storage.list_keys():
                path = blob_path(destination, key)
                path.write_bytes(storage.get(key))
                manifest['objects'].append({'key': key, 'sha256': file_digest(path),
                                            'bytes': path.stat().st_size})
            objects = {item['key']: item for item in manifest['objects']}
            references = db.execute(text("""
                SELECT object_key,sha256,byte_size FROM kamartha.attachments
                WHERE state IN ('STAGED','LINKED')
            """)).mappings()
            for row in references:
                item = objects.get(row['object_key'])
                if item is None or item['sha256'] != row['sha256'].strip() or item['bytes'] != row['byte_size']:
                    raise BackupError('Attachment metadata does not match backed-up Storage bytes.')
        # Only this final manifest marks a completed backup. Partial runs remain diagnostic evidence.
        (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        return manifest
    finally:
        engine.dispose()


def verify_backup(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format') != 1 or set(manifest.get('dumps', {})) != {'database.dump', 'revision.dump'}:
        raise BackupError('Unsupported backup manifest.')
    for filename, checksum in manifest['dumps'].items():
        verify_file(directory / filename, checksum)
    keys = set()
    for item in manifest['objects']:
        if item['key'] in keys:
            raise BackupError('Duplicate object key in manifest.')
        keys.add(item['key'])
        path = blob_path(directory, item['key'])
        verify_file(path, item['sha256'])
        if path.stat().st_size != item['bytes']:
            raise BackupError('Storage object size mismatch.')
    return manifest


def restore_database(url, directory, pg_bin):
    url = validate_restore_target(url)
    manifest = verify_backup(directory)
    engine = create_engine(url, hide_parameters=True, connect_args={'connect_timeout': 15})
    try:
        with engine.connect() as db:
            if db.scalar(text("SELECT to_regnamespace('kamartha') IS NOT NULL OR "
                              "to_regclass('public.alembic_version') IS NOT NULL")):
                raise BackupError('Restore target must be empty; no existing data will be overwritten.')
        for filename in ('database.dump', 'revision.dump'):
            pg_run(pg_bin, 'pg_restore', url, '--exit-on-error', '--no-owner', '--no-privileges',
                   '--single-transaction', '--dbname=' + url.database, Path(directory) / filename)
        with engine.connect() as db:
            db.execute(text("SET timezone='UTC'"))
            db.execute(text("SET datestyle='ISO, YMD'"))
            if table_fingerprints(db) != manifest['tables']:
                raise BackupError('Restored table fingerprints differ from backup snapshot.')
            if db.scalar(text('SELECT version_num FROM public.alembic_version')) != manifest['revision']:
                raise BackupError('Restored migration revision differs.')
        return manifest
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'verify', 'restore-test'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--pg-bin', type=Path, default=Path(
        os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\17\bin')))
    args = parser.parse_args()
    if args.action == 'verify':
        manifest = verify_backup(args.directory)
    elif args.action == 'restore-test':
        if os.environ.get('CONFIRM_ISOLATED_TEST_DATABASE') != 'yes':
            raise BackupError('Set CONFIRM_ISOLATED_TEST_DATABASE=yes for the isolated restore destination.')
        manifest = restore_database(os.environ['TEST_DATABASE_URL'], args.directory, args.pg_bin)
    else:
        from dotenv import dotenv_values
        values = dotenv_values(ROOT / 'backend' / '.env', interpolate=False)
        needed = ['SUPABASE_MIGRATION_DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
        if any(not values.get(key) for key in needed):
            raise BackupError('Supabase backup configuration is incomplete.')
        storage = BucketReader(values['SUPABASE_URL'], values['SUPABASE_SERVICE_KEY'],
                               values.get('STORAGE_BUCKET') or 'kamartha-files')
        try:
            manifest = create_backup(values['SUPABASE_MIGRATION_DATABASE_URL'], storage,
                                     args.directory, args.pg_bin)
        finally:
            storage.close()
    print(f"Backup {args.action}: PASS; revision={manifest['revision']}; "
          f"tables={len(manifest['tables'])}; objects={len(manifest['objects'])}.")
    print('Object bytes are verified locally; no production Storage restore was performed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Backup failed ({type(error).__name__}); no secrets printed. '
              'Do not treat an incomplete directory as a successful backup.', file=sys.stderr)
        raise SystemExit(1)
